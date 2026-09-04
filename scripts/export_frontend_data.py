"""Export presentation-data v1 from canonical GOLDs into browser-ready JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from src.config import (
    ATLAS_FACT_PATH,
    ATLAS_MONTH_PROFILE_PATH,
    ATLAS_SNAPSHOT_PATH,
    ATLAS_TYPE_SUMMARY_PATH,
    GOLD_DIR,
    MAPBIOMAS_CHANGE_PATH,
    MAPBIOMAS_SNAPSHOT_PATH,
    MUNIC_GOLD_PATH,
    PROJECT_ROOT,
)
from src.contracts.presentation import (
    ATLAS_RAIN_COBRADE_CODES,
    ATLAS_RAIN_TYPE_IDS,
    PRESENTATION_SCHEMA_VERSION,
    validate_presentation_payload,
)


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "app" / "public" / "data" / "v1"
DEFAULT_LEGACY_MUNICIPALITIES = PROJECT_ROOT / "app" / "public" / "data" / "municipios.json"
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"
GENERATED_MARKER = ".presentation-v1-generated"
MAX_SHARD_BYTES = 24 * 1024 * 1024
ATLAS_RAIN_CATALOG = [
    {"atlas_type_id": 1, "name": "Alagamentos", "cobrade_codes": ["12300"]},
    {"atlas_type_id": 2, "name": "Enxurradas", "cobrade_codes": ["12200"]},
    {"atlas_type_id": 7, "name": "Inundações", "cobrade_codes": ["12100"]},
    {"atlas_type_id": 8, "name": "Movimento de Massa", "cobrade_codes": ["11311", "11312", "11313", "11314", "11321", "11331", "11332", "11340"]},
    {"atlas_type_id": 13, "name": "Chuvas Intensas", "cobrade_codes": ["13214"]},
]
ATLAS_CATALOG_BY_TYPE = {item["atlas_type_id"]: item for item in ATLAS_RAIN_CATALOG}
ATLAS_TYPE_BY_COBRADE = {
    code: item["atlas_type_id"]
    for item in ATLAS_RAIN_CATALOG
    for code in item["cobrade_codes"]
}
if tuple(item["atlas_type_id"] for item in ATLAS_RAIN_CATALOG) != ATLAS_RAIN_TYPE_IDS or set(ATLAS_TYPE_BY_COBRADE) != ATLAS_RAIN_COBRADE_CODES:
    raise RuntimeError("Catalogo Atlas de chuva diverge do contrato v1")

GOLD_PATHS = {
    "dim": GOLD_DIR / "dim_municipality.parquet",
    "atlas_snapshot": ATLAS_SNAPSHOT_PATH,
    "atlas_types": ATLAS_TYPE_SUMMARY_PATH,
    "atlas_months": ATLAS_MONTH_PROFILE_PATH,
    "atlas_fact": ATLAS_FACT_PATH,
    "mapbiomas_snapshot": MAPBIOMAS_SNAPSHOT_PATH,
    "mapbiomas_change": MAPBIOMAS_CHANGE_PATH,
    "munic": MUNIC_GOLD_PATH,
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_paths(paths: dict[str, Path]) -> None:
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "GOLDs obrigatorias nao materializadas: " + ", ".join(sorted(missing))
        )


def _verify_manifest_hashes(project_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifests = {
        source: _load_json(
            project_root / "data" / "manifests" / source / "latest_successful_run.json"
        )
        for source in ("atlas", "mapbiomas", "munic")
    }
    errors = []
    for source, manifest in manifests.items():
        for relative_path, expected_hash in manifest.get("output_hashes", {}).items():
            if not relative_path.startswith("data/gold/"):
                continue
            path = project_root / relative_path
            actual_hash = _file_sha256(path) if path.is_file() else None
            if actual_hash != expected_hash:
                errors.append(
                    f"{source}:{relative_path} esperado={expected_hash} atual={actual_hash}"
                )
    if errors:
        raise RuntimeError("Hashes GOLD divergem dos manifests:\n" + "\n".join(errors))
    return manifests["atlas"], manifests["mapbiomas"], manifests["munic"]


def _as_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | str | int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON de apresentacao nao aceita numeros nao finitos")
        return int(value) if value.is_integer() else value
    if isinstance(value, Decimal):
        return _as_json_value(float(value))
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_as_json_value(item) for item in value]
    raise TypeError(f"Valor nao serializavel no contrato: {type(value)!r}")


def _rows_as_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [description[0] for description in cursor.description]
    return [
        {column: _as_json_value(value) for column, value in zip(columns, row, strict=True)}
        for row in cursor.fetchall()
    ]


def _path_sql(path: Path) -> str:
    return str(path).replace("'", "''")


def _load_legacy_municipalities(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Payload legado municipal deve ser uma lista JSON")
    by_code: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("code"), str):
            raise ValueError("Payload legado possui codigo municipal invalido")
        code = row["code"]
        if code in by_code:
            raise ValueError(f"Payload legado possui codigo duplicado: {code}")
        by_code[code] = row
    return by_code


def _transitional_census(legacy: dict[str, Any] | None) -> dict[str, Any]:
    if legacy is None:
        return {
            "state": "not_in_legacy_universe",
            "provenance": "transitional_legacy",
            "year": None,
            "connected_sewer_pct": None,
            "outside_selected_sewer_pct": None,
        }
    census = legacy.get("census")
    if not isinstance(census, dict):
        raise ValueError(f"Censo legado invalido para {legacy['code']}")
    connected = census.get("connectedSewerPct")
    outside = census.get("outsideSelectedSewerPct")
    if connected is None or outside is None:
        state = "not_published"
    else:
        state = "record"
    return {
        "state": state,
        "provenance": "transitional_legacy",
        "year": census.get("year"),
        "connected_sewer_pct": connected,
        "outside_selected_sewer_pct": outside,
    }


def _transitional_transfers(legacy: dict[str, Any] | None) -> dict[str, Any]:
    if legacy is None:
        return {
            "state": "not_in_legacy_universe",
            "provenance": "transitional_legacy",
            "legacy": None,
        }
    transfers = legacy.get("transfers")
    if transfers is not None and not isinstance(transfers, dict):
        raise ValueError(f"Transferegov legado invalido para {legacy['code']}")
    return {
        "state": "record" if transfers is not None else "no_record",
        "provenance": "transitional_legacy",
        "legacy": transfers,
    }


def _metadata(
    *,
    project_root: Path,
    atlas_manifest: dict[str, Any],
    mapbiomas_manifest: dict[str, Any],
    munic_manifest: dict[str, Any],
    atlas_catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    ibge_report = _load_json(project_root / "data" / "gold" / "data_quality_report.json")
    atlas_report = _load_json(project_root / "data" / "gold" / "atlas_data_quality_report.json")
    atlas_signature = atlas_manifest.get("input_signature", {})
    return {
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "territorial_universe": {
            "id": "ibge_current_5571",
            "municipality_count": ibge_report["number_of_rows"],
            "reference": "IBGE API de Localidades v1",
        },
        "sources": {
            "ibge": {
                "source": ibge_report["source"],
                "query_date": ibge_report["source_query_date"],
                "status": ibge_report["status"],
            },
            "atlas": {
                "release": atlas_manifest["source_release"],
                "official_date": atlas_signature.get("source_official_date"),
                "first_year": int(
                    atlas_report["source_inspection"]["first_event_date"][:4]
                ),
                "latest_year": int(
                    atlas_report["source_inspection"]["latest_event_date"][:4]
                ),
                "materialized_at": atlas_manifest["finished_at"],
                "source_sha256": atlas_manifest["source_hashes"]["csv"],
                "manifest": "data/manifests/atlas/latest_successful_run.json",
                "catalog": atlas_catalog,
            },
            "mapbiomas": {
                "collection_id": mapbiomas_manifest["collection_id"],
                "collection_version": mapbiomas_manifest["collection_version"],
                "first_year": mapbiomas_manifest["first_year"],
                "latest_year": mapbiomas_manifest["latest_year"],
                "materialized_at": mapbiomas_manifest["finished_at"],
                "source_sha256": mapbiomas_manifest["source_hashes"][
                    "statistics"
                ],
                "manifest": "data/manifests/mapbiomas/latest_successful_run.json",
            },
            "munic": {
                "reference_year": munic_manifest["source"]["reference_year"],
                "materialized_at": munic_manifest["generated_at"],
                "source_sha256": munic_manifest["source"]["sha256"],
                "manifest": "data/manifests/munic/latest_successful_run.json",
                "state": "self_reported",
            },
            "census": {
                "state": "transitional_legacy",
                "reference": "Censo 2022 / SIDRA 6805",
            },
            "transferegov": {
                "state": "transitional_legacy",
                "reference": "Payload publicado legado",
            },
        },
    }


def _load_gold_rows(connection: duckdb.DuckDBPyConnection, paths: dict[str, Path]) -> dict[str, Any]:
    dim_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, municipio, municipio_normalized, sigla_uf AS uf,
                   regiao, regiao_imediata, codigo_regiao_imediata, tipo_unidade_territorial
            FROM read_parquet('{_path_sql(paths['dim'])}')
            ORDER BY sigla_uf, municipio, codigo_ibge
            """
        )
    )
    snapshot_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, first_event_date::VARCHAR AS first_event_date,
                    latest_event_date::VARCHAR AS latest_event_date, event_count,
                    rain_related_event_count, reference_date::VARCHAR AS reference_date,
                    rain_related_event_count_10y, deaths, injured, homeless, displaced
            FROM read_parquet('{_path_sql(paths['atlas_snapshot'])}')
            """
        )
    )
    type_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, cobrade_code, first_event_date::VARCHAR AS first_event_date,
                   latest_event_date::VARCHAR AS latest_event_date, event_count, deaths,
                   injured, homeless, displaced, reported_affected_total
            FROM read_parquet('{_path_sql(paths['atlas_types'])}')
            """
        )
    )
    month_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, month, event_count, rain_related_event_count
            FROM read_parquet('{_path_sql(paths['atlas_months'])}')
            """
        )
    )
    fact_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, cobrade_code, atlas_type_id, min(atlas_type_name_source) AS type_name,
                   count(*) FILTER (WHERE is_federally_recognized) AS recognized_event_count,
                   sum(missing) AS missing
            FROM read_parquet('{_path_sql(paths['atlas_fact'])}')
            WHERE is_rain_related
            GROUP BY codigo_ibge, cobrade_code, atlas_type_id
            """
        )
    )
    annual_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, event_year AS year, atlas_type_id, count(*) AS event_count
            FROM read_parquet('{_path_sql(paths['atlas_fact'])}')
            WHERE is_rain_related
            GROUP BY codigo_ibge, event_year, atlas_type_id
            """
        )
    )
    land_cover_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, year, mapped_area_ha, urban_area_ha, urban_area_pct,
                    native_vegetation_area_ha, native_vegetation_area_pct,
                    agriculture_livestock_area_ha, agriculture_livestock_area_pct, water_area_ha,
                    water_area_pct, wetland_area_ha, wetland_area_pct
            FROM read_parquet('{_path_sql(paths['mapbiomas_snapshot'])}')
            ORDER BY codigo_ibge, year
            """
        )
    )
    change_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, first_year, latest_year, reference_year_5y,
                   reference_year_10y, reference_year_20y, urban_area_first_year_ha,
                   urban_area_latest_year_ha, urban_area_change_ha, urban_area_change_pct,
                   urban_change_5y_ha, urban_change_5y_pct, urban_change_10y_ha,
                   urban_change_10y_pct, urban_change_20y_ha, urban_change_20y_pct,
                   native_vegetation_first_year_ha, native_vegetation_latest_year_ha,
                   native_vegetation_change_ha, native_vegetation_change_pct,
                   native_vegetation_change_5y_ha, native_vegetation_change_5y_pct,
                   native_vegetation_change_10y_ha, native_vegetation_change_10y_pct,
                   native_vegetation_change_20y_ha, native_vegetation_change_20y_pct,
                   water_area_change_10y_ha, wetland_area_change_10y_ha
            FROM read_parquet('{_path_sql(paths['mapbiomas_change'])}')
            """
        )
    )
    munic_rows = _rows_as_dicts(
        connection.execute(
            f"""
            SELECT codigo_ibge, in_source,
                   municipal_civil_defense_body_status,
                   civil_defense_budget_provision_status,
                   any_risk_prevention_planning_instrument_status,
                   flood_risk_mapping_status, flood_contingency_plan_status,
                   flood_early_warning_status, landslide_risk_mapping_status,
                   landslide_contingency_plan_status, landslide_early_warning_status,
                   source_year
            FROM read_parquet('{_path_sql(paths['munic'])}')
            """
        )
    )
    return {
        "dim": dim_rows,
        "snapshot": {row["codigo_ibge"]: row for row in snapshot_rows},
        "types": type_rows,
        "months": month_rows,
        "fact_types": {
            (row["codigo_ibge"], row["cobrade_code"]): row for row in fact_rows
        },
        "annual": annual_rows,
        "atlas_catalog": ATLAS_RAIN_CATALOG,
        "land_cover": land_cover_rows,
        "change": {row["codigo_ibge"]: row for row in change_rows},
        "munic": {row["codigo_ibge"]: row for row in munic_rows},
    }


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _benchmark_metric(
    *, source: str, unit: str, reference: dict[str, Any], value: float | int | None,
    state: str, region_values: list[tuple[float | int | None, str]], municipality_count: int,
) -> dict[str, Any]:
    included_values = [float(candidate) for candidate, candidate_state in region_values if candidate_state == "included"]
    denominator = {
        "included": len(included_values),
        "missing": sum(candidate_state == "missing" for _, candidate_state in region_values),
        "undefined": sum(candidate_state == "undefined" for _, candidate_state in region_values),
    }
    if sum(denominator.values()) != municipality_count:
        raise ValueError("Denominadores do benchmark nao reconciliam com a regiao")
    comparable = state == "included" and included_values
    return {
        "source": source,
        "unit": unit,
        "reference": reference,
        "municipality_value": value,
        "mean": sum(included_values) / len(included_values) if included_values else None,
        "median": _median(included_values) if included_values else None,
        "percentile_strictly_lower_pct": (
            sum(candidate < float(value) for candidate in included_values) / len(included_values) * 100
            if comparable else None
        ),
        "denominator": denominator,
    }


def _prepare_immediate_region_benchmarks(gold: dict[str, Any]) -> None:
    """Pre-calculate the five regional comparisons from canonical GOLD rows."""
    members: dict[str, list[dict[str, Any]]] = {}
    for municipality in gold["dim"]:
        members.setdefault(municipality["codigo_regiao_imediata"], []).append(municipality)
    reference_dates = {row["reference_date"] for row in gold["snapshot"].values()}
    if len(reference_dates) != 1:
        raise ValueError("Snapshot Atlas possui datas de referencia divergentes")
    reference_date = reference_dates.pop()
    rain_counts = {
        code: row["rain_related_event_count_10y"]
        for code, row in gold["snapshot"].items()
    }
    snapshots_by_code: dict[str, list[dict[str, Any]]] = {}
    for row in gold["land_cover"]:
        snapshots_by_code.setdefault(row["codigo_ibge"], []).append(row)

    def map_value(code: str, metric: str) -> tuple[float | None, str, dict[str, Any]]:
        history = snapshots_by_code.get(code, [])
        if not history:
            return None, "missing", {"latest_snapshot_year": None}
        latest = history[-1]
        if metric in {"urban_area_pct", "native_vegetation_area_pct"}:
            if not latest["mapped_area_ha"] or latest[metric] is None:
                return None, "undefined", {"latest_snapshot_year": latest["year"]}
            return latest[metric], "included", {"latest_snapshot_year": latest["year"]}
        change = gold["change"].get(code)
        if not change or change.get("reference_year_20y") is None:
            return None, "undefined", {"reference_year_20y": None, "latest_snapshot_year": latest["year"]}
        baseline = next((row for row in history if row["year"] == change["reference_year_20y"]), None)
        base_area = baseline["urban_area_ha" if metric == "urban_change_20y_pct" else "native_vegetation_area_ha"] if baseline else None
        if not latest["mapped_area_ha"] or not base_area or change[metric] is None:
            return None, "undefined", {"reference_year_20y": change["reference_year_20y"], "latest_snapshot_year": latest["year"]}
        return change[metric], "included", {"reference_year_20y": change["reference_year_20y"], "latest_snapshot_year": latest["year"]}

    benchmarks: dict[str, dict[str, Any]] = {}
    for region_code, region_members in members.items():
        count = len(region_members)
        metric_values = {
            "rain_related_event_count_10y": [(rain_counts.get(item["codigo_ibge"], 0), "included") for item in region_members],
            **{metric: [map_value(item["codigo_ibge"], metric)[:2] for item in region_members] for metric in ("urban_change_20y_pct", "native_vegetation_change_20y_pct", "urban_area_pct", "native_vegetation_area_pct")},
        }
        for municipality in region_members:
            code = municipality["codigo_ibge"]
            maps = {metric: map_value(code, metric) for metric in metric_values if metric != "rain_related_event_count_10y"}
            benchmarks[code] = {
                "immediate_region": {
                    "codigo": region_code, "nome": municipality["regiao_imediata"],
                    "municipality_count": count, "includes_selected_municipality": True,
                    "metrics": {
                        "rain_related_event_count_10y": _benchmark_metric(source="Atlas Digital de Desastres/S2ID", unit="registros", reference={"window_years": 10, "reference_date": reference_date}, value=rain_counts[code], state="included", region_values=metric_values["rain_related_event_count_10y"], municipality_count=count),
                        **{metric: _benchmark_metric(source="MapBiomas Brasil", unit="percentual", reference=details[2], value=details[0], state=details[1], region_values=metric_values[metric], municipality_count=count) for metric, details in maps.items()},
                    },
                }
            }
    gold["immediate_region_benchmarks"] = benchmarks


def _annual_history(
    gold: dict[str, Any], municipality: dict[str, Any], rain_count: int
) -> dict[str, Any]:
    """Annual municipal counts and immediate-region averages over every municipality.

    The denominator is the complete current IBGE immediate-region membership;
    municipalities without a qualifying Atlas event contribute zero.
    """
    region_code = municipality["codigo_regiao_imediata"]
    members = gold["annual_members"][region_code]
    years = gold["annual_years"]
    counts = gold["annual_counts"]
    series = []
    for type_id in [None, *[row["atlas_type_id"] for row in gold["atlas_catalog"]]]:
        points = []
        for year in years:
            municipal_count = counts.get((municipality["codigo_ibge"], year, type_id), 0)
            regional_total = sum(counts.get((code, year, type_id), 0) for code in members)
            points.append(
                {
                    "year": year,
                    "municipal_event_count": municipal_count,
                    "immediate_region_average_event_count": regional_total / len(members),
                }
            )
        series.append({"atlas_type_id": type_id, "points": points})
    return {
        "first_year": years[0] if years else None,
        "latest_year": years[-1] if years else None,
        "benchmark": {
            "immediate_region": {
                "codigo": region_code,
                "nome": municipality["regiao_imediata"],
                "municipality_count": len(members),
                "zeros_policy": "included_as_zero",
            }
        },
        "series": series,
    }


def _prepare_annual_history(gold: dict[str, Any]) -> None:
    members: dict[str, list[str]] = {}
    for municipality in gold["dim"]:
        members.setdefault(municipality["codigo_regiao_imediata"], []).append(
            municipality["codigo_ibge"]
        )
    counts: dict[tuple[str, int, int | None], int] = {}
    observed_years = []
    for row in gold["annual"]:
        year = row["year"]
        if year is None:
            continue
        observed_years.append(year)
        key = (row["codigo_ibge"], year, row["atlas_type_id"])
        counts[key] = counts.get(key, 0) + row["event_count"]
        total_key = (row["codigo_ibge"], year, None)
        counts[total_key] = counts.get(total_key, 0) + row["event_count"]
    gold["annual_members"] = members
    gold["annual_counts"] = counts
    gold["annual_years"] = (
        list(range(min(observed_years), max(observed_years) + 1)) if observed_years else []
    )


def _summary_30_seconds(
    *,
    municipality: dict[str, Any],
    disaster_state: str,
    rain_count: int,
    first_event_date: str | None,
    latest_event_date: str | None,
    primary_type: str | None,
    land_cover_history: list[dict[str, Any]],
) -> str:
    """Build the municipal opening copy from published values only."""

    if disaster_state == "no_record":
        return "Nenhum registro foi encontrado nesta release do Atlas/S2ID."

    first_year = first_event_date[:4] if first_event_date else None
    latest_year = latest_event_date[:4] if latest_event_date else None
    record_label = "registro" if rain_count == 1 else "registros"
    atlas_copy = (
        f"Desde {first_year}, foram encontrados {rain_count} {record_label} "
        f"relacionados à chuva em {municipality['municipio']}."
    )
    if primary_type:
        atlas_copy += f" {primary_type} é o tipo mais frequente na série consultada."
    if latest_year:
        atlas_copy += f" O registro mais recente é de {latest_year}."

    if len(land_cover_history) < 2:
        return atlas_copy
    first, latest = land_cover_history[0], land_cover_history[-1]
    required = ("urban_area_ha",)
    if any(first[field] is None or latest[field] is None for field in required):
        return atlas_copy
    return (
        f"{atlas_copy} No território, a área classificada como urbanizada passou de "
        f"{first['urban_area_ha'] / 100:.2f} km² em {first['year']} para "
        f"{latest['urban_area_ha'] / 100:.2f} km² em {latest['year']}."
    )


def _payloads(
    gold: dict[str, Any], legacy_by_code: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    _prepare_annual_history(gold)
    _prepare_immediate_region_benchmarks(gold)
    invalid_fact_types = {
        (row["atlas_type_id"], row["cobrade_code"])
        for row in gold["fact_types"].values()
        if row["atlas_type_id"] not in ATLAS_RAIN_TYPE_IDS
        or ATLAS_TYPE_BY_COBRADE.get(row["cobrade_code"]) != row["atlas_type_id"]
    }
    if invalid_fact_types:
        raise ValueError(f"Eventos Atlas fora do catalogo oficial: {sorted(invalid_fact_types)}")

    types_by_code: dict[str, list[dict[str, Any]]] = {}
    for row in gold["types"]:
        fact_type = gold["fact_types"].get(
            (row["codigo_ibge"], row["cobrade_code"])
        )
        if fact_type is None:
            continue
        type_id = fact_type["atlas_type_id"]
        catalog = ATLAS_CATALOG_BY_TYPE.get(type_id)
        if catalog is None or row["cobrade_code"] not in catalog["cobrade_codes"]:
            raise ValueError(f"Resumo Atlas fora do catalogo oficial: {row['cobrade_code']}")
        items = types_by_code.setdefault(row["codigo_ibge"], [])
        item = next((candidate for candidate in items if candidate["atlas_type_id"] == type_id), None)
        if item is None:
            item = {
                "codigo_ibge": row["codigo_ibge"],
                "atlas_type_id": type_id,
                "type_name": catalog["name"],
                "cobrade_codes": catalog["cobrade_codes"],
                "first_event_date": row["first_event_date"],
                "latest_event_date": row["latest_event_date"],
                "event_count": 0,
                "deaths": 0,
                "injured": 0,
                "homeless": 0,
                "displaced": 0,
                "missing": 0,
                "recognized_event_count": 0,
                "reported_affected_total": 0,
            }
            items.append(item)
        item["first_event_date"] = min(item["first_event_date"], row["first_event_date"])
        item["latest_event_date"] = max(item["latest_event_date"], row["latest_event_date"])
        for field in ("event_count", "deaths", "injured", "homeless", "displaced", "reported_affected_total"):
            item[field] += row[field] or 0
        item["missing"] += fact_type["missing"] or 0
        item["recognized_event_count"] += fact_type["recognized_event_count"] or 0

    months_by_code: dict[str, dict[int, dict[str, Any]]] = {}
    for row in gold["months"]:
        code = row["codigo_ibge"]
        month = row["month"]
        if month in months_by_code.setdefault(code, {}):
            raise ValueError(f"Perfil mensal Atlas duplicado para {code}/{month}")
        months_by_code[code][month] = row

    land_cover_by_code: dict[str, list[dict[str, Any]]] = {}
    for row in gold["land_cover"]:
        land_cover_by_code.setdefault(row["codigo_ibge"], []).append(row)

    payloads = []
    for municipality in gold["dim"]:
        code = municipality["codigo_ibge"]
        snapshot = gold["snapshot"].get(code)
        if snapshot is None:
            raise ValueError(f"Snapshot Atlas ausente para {code}")
        rain_count = snapshot["rain_related_event_count"]
        disaster_state = "record" if rain_count > 0 else "no_record"
        recognized_count = sum(
            item["recognized_event_count"] for item in types_by_code.get(code, [])
        )
        observed_types = {item["atlas_type_id"]: item for item in types_by_code.get(code, [])}
        rain_types = []
        for catalog in ATLAS_RAIN_CATALOG:
            item = observed_types.get(catalog["atlas_type_id"])
            if item is None:
                item = {
                    "codigo_ibge": code,
                    "atlas_type_id": catalog["atlas_type_id"],
                    "type_name": catalog["name"],
                    "cobrade_codes": catalog["cobrade_codes"],
                    "first_event_date": None,
                    "latest_event_date": None,
                    "event_count": 0,
                    "deaths": 0,
                    "injured": 0,
                    "homeless": 0,
                    "displaced": 0,
                    "missing": 0,
                    "recognized_event_count": 0,
                    "reported_affected_total": 0,
                }
            rain_types.append(item)
        rain_types.sort(key=lambda item: (-item["event_count"], item["atlas_type_id"]))
        rain_impacts = {
            field: sum(item[field] for item in rain_types)
            for field in ("deaths", "injured", "homeless", "displaced")
        }
        rain_impacts["missing"] = sum(item["missing"] for item in rain_types)
        rain_impacts["reported_affected_total"] = sum(
            item["reported_affected_total"] or 0 for item in rain_types
        )
        for item in rain_types:
            item["event_pct"] = (item["event_count"] / rain_count * 100) if rain_count else 0
        rain_dates = [item["first_event_date"] for item in rain_types if item["first_event_date"]]
        latest_rain_dates = [item["latest_event_date"] for item in rain_types if item["latest_event_date"]]
        months = []
        for month in range(1, 13):
            row = months_by_code.get(code, {}).get(month)
            months.append(
                {
                    "month": month,
                    "event_count": row["event_count"] if row else 0,
                    "rain_related_event_count": row["rain_related_event_count"]
                    if row
                    else 0,
                    "event_pct": (
                        (row["rain_related_event_count"] if row else 0) / rain_count * 100
                        if rain_count
                        else None
                    ),
                }
            )

        land_cover_history = land_cover_by_code.get(code, [])
        land_cover_state = "record" if land_cover_history else "no_coverage"
        change = gold["change"].get(code)
        if land_cover_state == "record" and change is None:
            raise ValueError(f"Change MapBiomas ausente para {code}")
        if land_cover_state == "no_coverage":
            change = None
        elif change is not None:
            change = {key: value for key, value in change.items() if key != "codigo_ibge"}
            history_years = {item["year"] for item in land_cover_history}
            for window in (5, 10, 20):
                reference_key = f"reference_year_{window}y"
                if change[reference_key] not in history_years:
                    change[reference_key] = None
                    for prefix in ("urban", "native_vegetation"):
                        change[f"{prefix}_change_{window}y_ha"] = None
                        change[f"{prefix}_change_{window}y_pct"] = None

        census = _transitional_census(legacy_by_code.get(code))
        transfers = _transitional_transfers(legacy_by_code.get(code))
        munic = gold["munic"].get(code)
        if munic is None:
            raise ValueError(f"MUNIC ausente para {code}")
        municipal_capacity = {
            "state": "record" if munic["in_source"] else "not_in_source",
            "provenance": "self_reported_munic_2020",
            "reference_year": munic["source_year"],
            "indicators": {
                field.removesuffix("_status"): munic[field]
                for field in (
                    "municipal_civil_defense_body_status",
                    "civil_defense_budget_provision_status",
                    "any_risk_prevention_planning_instrument_status",
                    "flood_risk_mapping_status",
                    "flood_contingency_plan_status",
                    "flood_early_warning_status",
                    "landslide_risk_mapping_status",
                    "landslide_contingency_plan_status",
                    "landslide_early_warning_status",
                )
            },
        }
        summary_text = _summary_30_seconds(
            municipality=municipality,
            disaster_state=disaster_state,
            rain_count=rain_count,
            first_event_date=min(rain_dates) if disaster_state == "record" else None,
            latest_event_date=max(latest_rain_dates) if disaster_state == "record" else None,
            primary_type=rain_types[0]["type_name"] if rain_types else None,
            land_cover_history=land_cover_history,
        )
        payload = {
            "schema_version": PRESENTATION_SCHEMA_VERSION,
            "municipality": municipality,
            "summary": {
                "territorial_universe": "ibge_current_5571",
                "thirty_second_text": summary_text,
                "source_states": {
                    "ibge": "record",
                    "atlas": disaster_state,
                    "mapbiomas": land_cover_state,
                    "munic": municipal_capacity["state"],
                    "census": census["state"],
                    "transferegov": transfers["state"],
                },
            },
            "disasters": {
                "state": disaster_state,
                "history": {
                    "state": disaster_state,
                    "record_scope": "five_rain_related_cobrade_typologies",
                    "all_event_count": snapshot["event_count"],
                    "rain_related_event_count": rain_count,
                    "recognized_event_count": recognized_count,
                    "first_event_date": min(rain_dates)
                    if disaster_state == "record"
                    else None,
                    "latest_event_date": max(latest_rain_dates)
                    if disaster_state == "record"
                    else None,
                    "human_impacts": rain_impacts,
                    "annual": _annual_history(gold, municipality, rain_count),
                },
                "types": rain_types,
                "months": months,
                "highlights": [],
            },
            "land_cover": {
                "state": land_cover_state,
                "history": land_cover_history,
                "change": change,
            },
            "municipal_capacity": municipal_capacity,
            "census": census,
            "transfers": transfers,
            "benchmarks": gold["immediate_region_benchmarks"][code],
            "sources": [
                "ibge",
                "atlas",
                "mapbiomas",
                "munic_2020",
                "census_transitional_legacy",
                "transferegov_transitional_legacy",
            ],
        }
        validate_presentation_payload(payload)
        payloads.append(payload)
    return payloads


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _shard_value(uf: str, municipalities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "uf": uf,
        "municipalities": municipalities,
    }


def _partition_uf_payloads(
    uf: str, municipalities: dict[str, dict[str, Any]], max_shard_bytes: int
) -> list[dict[str, dict[str, Any]]]:
    """Pack complete municipal payloads into deterministic, deployable UF shards."""
    prefix = b'{"municipalities":{'
    suffix = (
        b'},"schema_version":'
        + json.dumps(PRESENTATION_SCHEMA_VERSION).encode("utf-8")
        + b',"uf":'
        + json.dumps(uf, ensure_ascii=False).encode("utf-8")
        + b'}\n'
    )
    fixed_size = len(prefix) + len(suffix)
    partitions: list[dict[str, dict[str, Any]]] = []
    current: dict[str, dict[str, Any]] = {}
    current_size = fixed_size
    for code in sorted(municipalities):
        payload = municipalities[code]
        entry = (
            json.dumps(code, ensure_ascii=False).encode("utf-8")
            + b":"
            + json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        individual = {code: payload}
        if fixed_size + len(entry) > max_shard_bytes:
            raise ValueError(
                f"Payload municipal {uf}/{code} excede o alvo de {max_shard_bytes} bytes"
            )
        entry_size = len(entry) + (1 if current else 0)
        if current and current_size + entry_size > max_shard_bytes:
            partitions.append(current)
            current = individual
            current_size = fixed_size + len(entry)
        else:
            current[code] = payload
            current_size += entry_size
    if current:
        partitions.append(current)
    return partitions


def _replace_output(staged: Path, output_dir: Path) -> None:
    if output_dir.exists():
        entries = {path.name for path in output_dir.iterdir()}
        if entries != {".gitkeep"} and not (output_dir / GENERATED_MARKER).is_file():
            raise RuntimeError(
                f"Recusando substituir diretorio nao gerado: {output_dir}"
            )
        shutil.rmtree(output_dir)
    staged.replace(output_dir)


def export_frontend_data(
    *,
    project_root: Path = PROJECT_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    legacy_municipalities_path: Path = DEFAULT_LEGACY_MUNICIPALITIES,
    expected_municipality_count: int | None = None,
    verify_manifest_hashes: bool = True,
    max_shard_bytes: int = MAX_SHARD_BYTES,
) -> dict[str, Any]:
    """Export v1 files and return deterministic counts and hashes."""

    if max_shard_bytes < 1:
        raise ValueError("max_shard_bytes deve ser positivo")
    paths = {
        name: project_root / path.relative_to(PROJECT_ROOT)
        for name, path in GOLD_PATHS.items()
    }
    _require_paths(paths)
    if not legacy_municipalities_path.is_file():
        raise FileNotFoundError(f"Payload legado ausente: {legacy_municipalities_path}")
    if verify_manifest_hashes:
        atlas_manifest, mapbiomas_manifest, munic_manifest = _verify_manifest_hashes(project_root)
    else:
        atlas_manifest = _load_json(
            project_root / "data" / "manifests" / "atlas" / "latest_successful_run.json"
        )
        mapbiomas_manifest = _load_json(
            project_root
            / "data"
            / "manifests"
            / "mapbiomas"
            / "latest_successful_run.json"
        )
        munic_manifest = _load_json(
            project_root / "data" / "manifests" / "munic" / "latest_successful_run.json"
        )

    connection = duckdb.connect(":memory:")
    try:
        gold = _load_gold_rows(connection, paths)
    finally:
        connection.close()
    municipality_codes = [row["codigo_ibge"] for row in gold["dim"]]
    if len(municipality_codes) != len(set(municipality_codes)):
        raise ValueError("dim_municipality possui codigo_ibge duplicado")
    if expected_municipality_count is not None and len(municipality_codes) != expected_municipality_count:
        raise ValueError(
            f"Indice possui {len(municipality_codes)} unidades; esperado {expected_municipality_count}"
        )

    payloads = _payloads(gold, _load_legacy_municipalities(legacy_municipalities_path))
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".presentation-v1-", dir=output_dir.parent
    ) as temporary_root:
        staged = Path(temporary_root) / "v1"
        staged.mkdir()
        (staged / GENERATED_MARKER).write_text("v1\n", encoding="ascii")
        (staged / ".gitkeep").touch()
        metadata = _metadata(
            project_root=project_root,
            atlas_manifest=atlas_manifest,
            mapbiomas_manifest=mapbiomas_manifest,
            munic_manifest=munic_manifest,
            atlas_catalog=gold["atlas_catalog"],
        )
        _write_json(staged / "metadata.json", metadata)

        payloads_by_uf: dict[str, dict[str, dict[str, Any]]] = {}
        for payload in payloads:
            municipality = payload["municipality"]
            code = municipality["codigo_ibge"]
            uf = municipality["uf"]
            payloads_by_uf.setdefault(uf, {})[code] = payload

        index_entries = []
        for uf, municipalities in sorted(payloads_by_uf.items()):
            partitions = _partition_uf_payloads(uf, municipalities, max_shard_bytes)
            multiple_parts = len(partitions) > 1
            for part_number, partition in enumerate(partitions, start=1):
                filename = f"{uf}-{part_number:03d}.json" if multiple_parts else f"{uf}.json"
                shard = f"/data/v1/uf/{filename}"
                for code in partition:
                    index_entries.append({**municipalities[code]["municipality"], "shard": shard})
                _write_json(staged / "uf" / filename, _shard_value(uf, partition))
        _write_json(
            staged / "municipal-index.json",
            {
                "schema_version": PRESENTATION_SCHEMA_VERSION,
                "territorial_universe": "ibge_current_5571",
                "municipalities": index_entries,
            },
        )
        _replace_output(staged, output_dir)

    generated_files = sorted(
        path for path in output_dir.rglob("*") if path.is_file() and path.name != GENERATED_MARKER
    )
    return {
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "municipalities": len(payloads),
        "ufs": len(payloads_by_uf),
        "files": len(generated_files),
        "output_dir": str(output_dir),
        "sha256": {
            path.relative_to(output_dir).as_posix(): _file_sha256(path)
            for path in generated_files
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--legacy-municipalities", type=Path, default=DEFAULT_LEGACY_MUNICIPALITIES
    )
    args = parser.parse_args()
    result = export_frontend_data(
        output_dir=args.output_dir,
        legacy_municipalities_path=args.legacy_municipalities,
        expected_municipality_count=5571,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
