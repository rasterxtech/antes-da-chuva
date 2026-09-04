"""Presentation-data v1 contract shared with the TypeScript frontend."""

from __future__ import annotations

import re
from typing import Any, Literal, TypedDict


PRESENTATION_SCHEMA_VERSION = "v1"
ATLAS_RAIN_TYPE_IDS = (1, 2, 7, 8, 13)
ATLAS_RAIN_COBRADE_CODES = frozenset(
    {"12300", "12200", "12100", "11311", "11312", "11313", "11314", "11321", "11331", "11332", "11340", "13214"}
)
PRESENTATION_STATES = frozenset(
    {
        "record",
        "no_record",
        "no_coverage",
        "not_published",
        "not_in_legacy_universe",
        "not_in_source",
    }
)

PresentationState = Literal[
    "record",
    "no_record",
    "no_coverage",
    "not_published",
    "not_in_legacy_universe",
    "not_in_source",
]


class MunicipalityIdentity(TypedDict):
    codigo_ibge: str
    municipio: str
    municipio_normalized: str
    uf: str
    regiao: str
    regiao_imediata: str
    codigo_regiao_imediata: str
    tipo_unidade_territorial: str


class MunicipalIndexEntry(MunicipalityIdentity):
    shard: str


class PresentationPayload(TypedDict):
    schema_version: Literal["v1"]
    municipality: MunicipalityIdentity
    summary: dict[str, Any]
    disasters: dict[str, Any]
    land_cover: dict[str, Any]
    municipal_capacity: dict[str, Any]
    census: dict[str, Any]
    transfers: dict[str, Any]
    benchmarks: dict[str, Any]
    sources: list[str]


def validate_presentation_payload(payload: dict[str, Any]) -> None:
    """Reject structural violations before a payload reaches the frontend."""

    required_sections = {
        "schema_version",
        "municipality",
        "summary",
        "disasters",
        "land_cover",
        "municipal_capacity",
        "census",
        "transfers",
        "benchmarks",
        "sources",
    }
    missing = required_sections - set(payload)
    if missing:
        raise ValueError(f"Payload de apresentacao sem secoes: {sorted(missing)}")
    if payload["schema_version"] != PRESENTATION_SCHEMA_VERSION:
        raise ValueError("Versao do contrato de apresentacao invalida")

    summary = payload["summary"]
    if (
        not isinstance(summary, dict)
        or summary.get("territorial_universe") != "ibge_current_5571"
        or not isinstance(summary.get("thirty_second_text"), str)
        or not summary["thirty_second_text"]
    ):
        raise ValueError("summary do resumo de 30 segundos invalido")

    municipality = payload["municipality"]
    if not isinstance(municipality, dict):
        raise ValueError("municipality deve ser um objeto")
    codigo_ibge = municipality.get("codigo_ibge")
    if not isinstance(codigo_ibge, str) or not re.fullmatch(r"\d{7}", codigo_ibge):
        raise ValueError("codigo_ibge deve ser texto com sete digitos")
    for field in (
        "municipio",
        "municipio_normalized",
        "uf",
        "regiao",
        "regiao_imediata",
        "codigo_regiao_imediata",
        "tipo_unidade_territorial",
    ):
        if not isinstance(municipality.get(field), str):
            raise ValueError(f"municipality.{field} deve ser texto")

    for section in ("disasters", "land_cover", "municipal_capacity", "census", "transfers"):
        value = payload[section]
        if not isinstance(value, dict) or value.get("state") not in PRESENTATION_STATES:
            raise ValueError(f"{section}.state invalido")

    history = payload["disasters"].get("history")
    if not isinstance(history, dict) or not isinstance(history.get("annual"), dict):
        raise ValueError("disasters.history.annual invalido")
    annual = history["annual"]
    benchmark = annual.get("benchmark")
    series = annual.get("series")
    if not isinstance(benchmark, dict) or not isinstance(series, list) or not series:
        raise ValueError("serie anual ou benchmark imediato invalido")
    immediate = benchmark.get("immediate_region")
    if not isinstance(immediate, dict) or immediate.get("zeros_policy") != "included_as_zero":
        raise ValueError("politica de zeros do benchmark imediato invalida")
    if not isinstance(immediate.get("municipality_count"), int) or immediate["municipality_count"] < 1:
        raise ValueError("benchmark imediato sem quantidade de municipios")

    first_year, latest_year = annual.get("first_year"), annual.get("latest_year")
    if not isinstance(first_year, int) or not isinstance(latest_year, int) or first_year > latest_year:
        raise ValueError("limites da serie anual invalidos")
    expected_years = list(range(first_year, latest_year + 1))
    expected_series_ids = {None, *ATLAS_RAIN_TYPE_IDS}
    if {item.get("atlas_type_id") for item in series if isinstance(item, dict)} != expected_series_ids:
        raise ValueError("serie anual deve conter total e os cinco atlas_type_ids")
    annual_by_type: dict[int | None, dict[int, int | float]] = {}
    for item in series:
        if not isinstance(item, dict) or item.get("atlas_type_id") not in expected_series_ids:
            raise ValueError("serie anual por tipo invalida")
        points = item.get("points")
        if not isinstance(points, list) or [point.get("year") for point in points if isinstance(point, dict)] != expected_years:
            raise ValueError("serie anual deve ser continua e ordenada")
        by_year: dict[int, int | float] = {}
        for point in points:
            if not isinstance(point, dict) or not isinstance(point.get("municipal_event_count"), (int, float)) or not isinstance(point.get("immediate_region_average_event_count"), (int, float)):
                raise ValueError("ponto da serie anual invalido")
            by_year[point["year"]] = point["municipal_event_count"]
        annual_by_type[item["atlas_type_id"]] = by_year
    if any(
        annual_by_type[None][year]
        != sum(annual_by_type[type_id][year] for type_id in ATLAS_RAIN_TYPE_IDS)
        for year in expected_years
    ):
        raise ValueError("serie anual total nao reconcilia com as tipologias")

    types = payload["disasters"].get("types")
    months = payload["disasters"].get("months")
    if not isinstance(types, list) or len(types) != 5:
        raise ValueError("disasters.types deve conter exatamente cinco tipologias")
    if {item.get("atlas_type_id") for item in types if isinstance(item, dict)} != set(ATLAS_RAIN_TYPE_IDS):
        raise ValueError("disasters.types deve conter os cinco atlas_type_ids oficiais")
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("event_pct"), (int, float))
        or not isinstance(item.get("cobrade_codes"), list)
        or not set(item["cobrade_codes"]).issubset(ATLAS_RAIN_COBRADE_CODES)
        for item in types
    ):
        raise ValueError("disasters.types.event_pct invalido")
    if sum(item["event_count"] for item in types) != history["rain_related_event_count"]:
        raise ValueError("disasters.types nao reconcilia com o total de chuva")
    for field in ("deaths", "injured", "homeless", "displaced", "missing", "reported_affected_total"):
        if sum(item.get(field, 0) or 0 for item in types) != history["human_impacts"].get(field):
            raise ValueError(f"impactos por tipo nao reconciliam: {field}")
    if not isinstance(months, list) or [item.get("month") for item in months] != list(range(1, 13)):
        raise ValueError("disasters.months deve conter exatamente os doze meses ordenados")
    if any(item.get("event_pct") is not None and not isinstance(item.get("event_pct"), (int, float)) for item in months):
        raise ValueError("disasters.months.event_pct invalido")
    if history.get("rain_related_event_count") == 0 and any(item.get("event_pct") is not None for item in months):
        raise ValueError("meses sem registros devem ter event_pct nulo")

    land_cover = payload["land_cover"]
    if land_cover["state"] == "no_coverage" and (land_cover.get("history") != [] or land_cover.get("change") is not None):
        raise ValueError("MapBiomas sem cobertura deve ter history vazia e change nulo")
    if land_cover["state"] == "record":
        history_years = [row.get("year") for row in land_cover.get("history", []) if isinstance(row, dict)]
        change = land_cover.get("change")
        if not history_years or not isinstance(change, dict):
            raise ValueError("MapBiomas com cobertura deve ter serie e variacoes")
        for window in (5, 10, 20):
            reference = change.get(f"reference_year_{window}y")
            if reference is not None and reference not in history_years:
                raise ValueError(f"janela MapBiomas {window}y sem ano de referencia na serie")

    if payload["census"].get("provenance") != "transitional_legacy":
        raise ValueError("census deve declarar proveniencia transicional")
    if payload["transfers"].get("provenance") != "transitional_legacy":
        raise ValueError("transfers deve declarar proveniencia transicional")
    capacity = payload["municipal_capacity"]
    if capacity.get("provenance") != "self_reported_munic_2020" or capacity.get("reference_year") != 2020:
        raise ValueError("municipal_capacity deve declarar proveniencia e referencia MUNIC 2020")
    expected_indicators = {
        "municipal_civil_defense_body",
        "civil_defense_budget_provision",
        "any_risk_prevention_planning_instrument",
        "flood_risk_mapping",
        "flood_contingency_plan",
        "flood_early_warning",
        "landslide_risk_mapping",
        "landslide_contingency_plan",
        "landslide_early_warning",
    }
    indicators = capacity.get("indicators")
    allowed_statuses = {
        "declared_yes", "declared_no", "refused", "not_reported",
        "not_applicable", "unknown", "not_in_source",
    }
    if not isinstance(indicators, dict) or set(indicators) != expected_indicators:
        raise ValueError("municipal_capacity possui indicadores invalidos")
    if any(value not in allowed_statuses for value in indicators.values()):
        raise ValueError("municipal_capacity possui status invalido")
    if capacity["state"] == "record" and "not_in_source" in indicators.values():
        raise ValueError("municipal_capacity com registro nao pode usar not_in_source")
    if capacity["state"] == "not_in_source" and set(indicators.values()) != {"not_in_source"}:
        raise ValueError("municipal_capacity fora da fonte deve explicitar todos os indicadores")
    immediate_benchmark = payload["benchmarks"].get("immediate_region") if isinstance(payload["benchmarks"], dict) else None
    if not isinstance(immediate_benchmark, dict) or immediate_benchmark.get("includes_selected_municipality") is not True:
        raise ValueError("benchmarks.immediate_region invalido")
    municipality_count = immediate_benchmark.get("municipality_count")
    metrics = immediate_benchmark.get("metrics")
    expected_metrics = {"rain_related_event_count_10y", "urban_change_20y_pct", "native_vegetation_change_20y_pct", "urban_area_pct", "native_vegetation_area_pct"}
    if not isinstance(municipality_count, int) or municipality_count < 1 or not isinstance(metrics, dict) or set(metrics) != expected_metrics:
        raise ValueError("metricas do benchmark imediato invalidas")
    for name, metric in metrics.items():
        if not isinstance(metric, dict) or not isinstance(metric.get("source"), str) or not isinstance(metric.get("unit"), str) or not isinstance(metric.get("reference"), dict):
            raise ValueError(f"benchmark {name} sem metadados obrigatorios")
        if any(metric.get(field) is not None and not isinstance(metric.get(field), (int, float)) for field in ("municipality_value", "mean", "median", "percentile_strictly_lower_pct")):
            raise ValueError(f"benchmark {name} possui valor invalido")
        denominator = metric.get("denominator")
        if not isinstance(denominator, dict) or any(not isinstance(denominator.get(field), int) or denominator[field] < 0 for field in ("included", "missing", "undefined")) or sum(denominator[field] for field in ("included", "missing", "undefined")) != municipality_count:
            raise ValueError(f"denominador do benchmark {name} invalido")
        if metric["denominator"]["included"] == 0 and any(metric.get(field) is not None for field in ("mean", "median", "percentile_strictly_lower_pct")):
            raise ValueError(f"benchmark {name} sem comparaveis nao pode ter resumo")
    if not all(isinstance(source, str) for source in payload["sources"]):
        raise ValueError("sources deve conter apenas identificadores textuais")
