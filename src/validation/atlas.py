from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from src.transform.atlas import SourceInspection


NONNEGATIVE_COLUMNS = (
    "deaths",
    "injured",
    "ill",
    "homeless",
    "displaced",
    "missing",
    "drought_affected",
    "direct_human_damage_total",
    "other_affected",
    "reported_affected_total",
    "housing_units_damaged",
    "housing_units_destroyed",
    "housing_damage_brl",
    "health_facilities_damaged",
    "health_facilities_destroyed",
    "health_facilities_damage_brl",
    "education_facilities_damaged",
    "education_facilities_destroyed",
    "education_facilities_damage_brl",
    "service_facilities_damaged",
    "service_facilities_destroyed",
    "service_facilities_damage_brl",
    "community_facilities_damaged",
    "community_facilities_destroyed",
    "community_facilities_damage_brl",
    "infrastructure_works_damaged",
    "infrastructure_works_destroyed",
    "infrastructure_damage_brl",
    "material_damage_total_brl",
    "public_health_emergency_loss_brl",
    "public_water_supply_loss_brl",
    "public_sewerage_loss_brl",
    "public_waste_management_loss_brl",
    "public_pest_control_loss_brl",
    "public_energy_distribution_loss_brl",
    "public_telecommunications_loss_brl",
    "public_transport_loss_brl",
    "public_fuel_distribution_loss_brl",
    "public_safety_loss_brl",
    "public_education_loss_brl",
    "public_loss_total_brl",
    "private_agriculture_loss_brl",
    "private_livestock_loss_brl",
    "private_industry_loss_brl",
    "private_commerce_loss_brl",
    "private_services_loss_brl",
    "private_loss_total_brl",
    "public_private_loss_total_brl",
)


def _scalar(connection: duckdb.DuckDBPyConnection, query: str) -> int | float:
    return connection.execute(query).fetchone()[0]


def _check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    observed: Any,
    expected: Any,
    passed: bool,
) -> None:
    checks.append(
        {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "observed": observed,
            "expected": expected,
        }
    )


def _duplicate_keys(
    connection: duckdb.DuckDBPyConnection, table: str, columns: tuple[str, ...]
) -> int:
    keys = ", ".join(columns)
    return int(
        _scalar(
            connection,
            f"SELECT count(*) FROM (SELECT {keys} FROM {table} "
            f"GROUP BY ALL HAVING count(*) > 1)",
        )
    )


def validate_atlas(
    connection: duckdb.DuckDBPyConnection,
    *,
    inspection: SourceInspection,
    source_release: str,
    source_official_date: str,
    source_first_year: int,
    source_latest_year: int,
    resources: dict[str, dict[str, Any]],
    dim_municipality_path: Path,
    generated_at: datetime,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    rows = {
        "raw": int(_scalar(connection, "SELECT count(*) FROM raw_atlas_event")),
        "silver": int(
            _scalar(connection, "SELECT count(*) FROM silver_disaster_event")
        ),
        "correction_factor": int(
            _scalar(
                connection, "SELECT count(*) FROM atlas_monetary_correction_factor"
            )
        ),
        "disaster_type": int(
            _scalar(connection, "SELECT count(*) FROM dim_disaster_type")
        ),
        "fact": int(_scalar(connection, "SELECT count(*) FROM fact_disaster_event")),
        "snapshot": int(
            _scalar(
                connection,
                "SELECT count(*) FROM snapshot_municipality_disaster_history",
            )
        ),
        "type_summary": int(
            _scalar(
                connection, "SELECT count(*) FROM municipality_disaster_type_summary"
            )
        ),
        "month_profile": int(
            _scalar(
                connection, "SELECT count(*) FROM municipality_disaster_month_profile"
            )
        ),
    }

    resource_bytes = {
        name: manifest["content_length"] for name, manifest in resources.items()
    }
    _check(
        checks,
        name="raw_resources_are_nonempty_and_readable",
        observed={"bytes": resource_bytes, "csv_rows": rows["raw"]},
        expected="all resource sizes and CSV row count > 0",
        passed=all(size > 0 for size in resource_bytes.values()) and rows["raw"] > 0,
    )

    workbook_reconciliation = connection.execute(
        """
        WITH csv_ids AS (
            SELECT Protocolo_S2iD AS source_event_id FROM raw_atlas_event
        )
        SELECT
            (SELECT count(*) FROM raw_atlas_original_workbook_ids),
            (SELECT count(*) FROM raw_atlas_corrected_workbook_ids),
            (SELECT count(*) FROM csv_ids
             ANTI JOIN raw_atlas_original_workbook_ids USING (source_event_id)),
            (SELECT count(*) FROM raw_atlas_original_workbook_ids
             ANTI JOIN csv_ids USING (source_event_id)),
            (SELECT count(*) FROM csv_ids
             ANTI JOIN raw_atlas_corrected_workbook_ids USING (source_event_id)),
            (SELECT count(*) FROM raw_atlas_corrected_workbook_ids
             ANTI JOIN csv_ids USING (source_event_id)),
            (SELECT count(*) FROM raw_atlas_corrected_workbook_comparison
             WHERE NOT all_fields_match)
        """
    ).fetchone()
    workbook_report = {
        "original_rows": workbook_reconciliation[0],
        "corrected_rows": workbook_reconciliation[1],
        "csv_ids_missing_from_original": workbook_reconciliation[2],
        "original_ids_missing_from_csv": workbook_reconciliation[3],
        "csv_ids_missing_from_corrected": workbook_reconciliation[4],
        "corrected_ids_missing_from_csv": workbook_reconciliation[5],
        "corrected_rows_with_value_differences": workbook_reconciliation[6],
    }
    _check(
        checks,
        name="csv_and_workbook_event_sets_reconcile",
        observed=workbook_report,
        expected={
            "original_rows": rows["raw"],
            "corrected_rows": rows["raw"],
            "csv_ids_missing_from_original": 0,
            "original_ids_missing_from_csv": 0,
            "csv_ids_missing_from_corrected": 0,
            "corrected_ids_missing_from_csv": 0,
            "corrected_rows_with_value_differences": 0,
        },
        passed=(
            workbook_reconciliation[0] == rows["raw"]
            and workbook_reconciliation[1] == rows["raw"]
            and all(value == 0 for value in workbook_reconciliation[2:])
        ),
    )

    date_profile = connection.execute(
        """
        SELECT
            min(event_year),
            max(event_year),
            count(*) FILTER (WHERE event_year <> year(event_date)),
            count(*) FILTER (WHERE event_month <> month(event_date)),
            count(*) FILTER (WHERE event_month NOT BETWEEN 1 AND 12)
        FROM silver_disaster_event
        """
    ).fetchone()
    _check(
        checks,
        name="event_dates_match_declared_release_and_derived_fields",
        observed={
            "first_year": date_profile[0],
            "latest_year": date_profile[1],
            "event_year_differences": date_profile[2],
            "event_month_differences": date_profile[3],
            "invalid_months": date_profile[4],
        },
        expected={
            "first_year": source_first_year,
            "latest_year": source_latest_year,
            "event_year_differences": 0,
            "event_month_differences": 0,
            "invalid_months": 0,
        },
        passed=date_profile
        == (source_first_year, source_latest_year, 0, 0, 0),
    )

    required_nulls = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE source_event_id IS NULL OR source_event_id = ''),
            count(*) FILTER (WHERE codigo_ibge IS NULL OR codigo_ibge = ''),
            count(*) FILTER (WHERE event_date IS NULL),
            count(*) FILTER (WHERE registration_date IS NULL),
            count(*) FILTER (WHERE cobrade_code IS NULL OR cobrade_code = ''),
            count(*) FILTER (WHERE status_source IS NULL OR status_source = '')
        FROM silver_disaster_event
        """
    ).fetchone()
    required_null_report = dict(
        zip(
            (
                "source_event_id",
                "codigo_ibge",
                "event_date",
                "registration_date",
                "cobrade_code",
                "status_source",
            ),
            required_nulls,
            strict=True,
        )
    )
    _check(
        checks,
        name="silver_required_fields_are_present",
        observed=required_null_report,
        expected={key: 0 for key in required_null_report},
        passed=all(value == 0 for value in required_null_report.values()),
    )

    silver_duplicate_ids = _duplicate_keys(
        connection, "silver_disaster_event", ("source_event_id",)
    )
    _check(
        checks,
        name="source_event_id_is_unique",
        observed=silver_duplicate_ids,
        expected=0,
        passed=silver_duplicate_ids == 0,
    )

    invalid_codes = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE NOT regexp_full_match(codigo_ibge, '[0-9]{7}')),
            count(*) FILTER (WHERE NOT regexp_full_match(cobrade_code, '[0-9]{5}'))
        FROM silver_disaster_event
        """
    ).fetchone()
    _check(
        checks,
        name="territorial_and_cobrade_codes_have_valid_shapes",
        observed={"codigo_ibge": invalid_codes[0], "cobrade_code": invalid_codes[1]},
        expected={"codigo_ibge": 0, "cobrade_code": 0},
        passed=invalid_codes == (0, 0),
    )

    negative_counts = {
        column: int(
            _scalar(
                connection,
                f"SELECT count(*) FROM silver_disaster_event WHERE {column} < 0",
            )
        )
        for column in NONNEGATIVE_COLUMNS
    }
    _check(
        checks,
        name="counts_and_monetary_values_are_nonnegative",
        observed={
            "columns_with_negative_values": {
                key: value for key, value in negative_counts.items() if value
            }
        },
        expected={"columns_with_negative_values": {}},
        passed=all(value == 0 for value in negative_counts.values()),
    )

    human_identity_differences = int(
        _scalar(
            connection,
            """
            SELECT count(*) FROM silver_disaster_event
            WHERE direct_human_damage_total <>
                deaths + injured + ill + homeless + displaced + missing + drought_affected
               OR reported_affected_total <> direct_human_damage_total + other_affected
            """,
        )
    )
    _check(
        checks,
        name="human_impact_totals_reconcile",
        observed=human_identity_differences,
        expected=0,
        passed=human_identity_differences == 0,
    )

    monetary_differences = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE abs(material_damage_total_brl - (
                housing_damage_brl + health_facilities_damage_brl
                + education_facilities_damage_brl + service_facilities_damage_brl
                + community_facilities_damage_brl + infrastructure_damage_brl
            )) > 0.05),
            count(*) FILTER (WHERE abs(public_loss_total_brl - (
                public_health_emergency_loss_brl + public_water_supply_loss_brl
                + public_sewerage_loss_brl + public_waste_management_loss_brl
                + public_pest_control_loss_brl + public_energy_distribution_loss_brl
                + public_telecommunications_loss_brl + public_transport_loss_brl
                + public_fuel_distribution_loss_brl + public_safety_loss_brl
                + public_education_loss_brl
            )) > 0.05),
            count(*) FILTER (WHERE abs(private_loss_total_brl - (
                private_agriculture_loss_brl + private_livestock_loss_brl
                + private_industry_loss_brl + private_commerce_loss_brl
                + private_services_loss_brl
            )) > 0.05),
            count(*) FILTER (WHERE abs(public_private_loss_total_brl - (
                public_loss_total_brl + private_loss_total_brl
            )) > 0.05)
        FROM silver_disaster_event
        """
    ).fetchone()
    monetary_report = dict(
        zip(
            ("material", "public", "private", "public_plus_private"),
            monetary_differences,
            strict=True,
        )
    )
    _check(
        checks,
        name="monetary_component_totals_reconcile_with_rounding_tolerance",
        observed=monetary_report,
        expected={key: 0 for key in monetary_report},
        passed=all(value == 0 for value in monetary_report.values()),
    )

    cobrade_checks = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE d.cobrade_code IS NULL),
            count(*) FILTER (WHERE d.cobrade_code IS NOT NULL AND (
                s.atlas_type_id <> d.atlas_type_id
                OR s.atlas_type_name_source <> d.atlas_type_name
                OR s.atlas_group_name_source <> d.atlas_group_name
                OR s.is_rain_related <> d.is_rain_related
            ))
        FROM silver_disaster_event s
        LEFT JOIN dim_disaster_type d USING (cobrade_code)
        """
    ).fetchone()
    _check(
        checks,
        name="cobrade_codes_and_classification_match_official_dimension",
        observed={"missing_codes": cobrade_checks[0], "mapping_conflicts": cobrade_checks[1]},
        expected={"missing_codes": 0, "mapping_conflicts": 0},
        passed=cobrade_checks == (0, 0),
    )

    correction_checks = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE reference_year BETWEEN 1991 AND 1994
                              AND correction_factor <> 0),
            count(*) FILTER (WHERE reference_year = 2025
                              AND (correction_factor <> 1
                                   OR abs(igp_di_december_index - 1167.239) > 1e-9))
        FROM atlas_monetary_correction_factor
        """
    ).fetchone()
    _check(
        checks,
        name="igp_di_correction_reference_is_consistent",
        observed={
            "nonzero_pre_real_factors": correction_checks[0],
            "invalid_2025_reference_rows": correction_checks[1],
        },
        expected={"nonzero_pre_real_factors": 0, "invalid_2025_reference_rows": 0},
        passed=correction_checks == (0, 0),
    )

    dim_path = str(dim_municipality_path).replace("'", "''")
    matching = connection.execute(
        f"""
        WITH source AS (
            SELECT DISTINCT codigo_ibge FROM silver_disaster_event
        ), dim AS (
            SELECT codigo_ibge FROM read_parquet('{dim_path}')
        ), matched AS (
            SELECT codigo_ibge FROM source INNER JOIN dim USING (codigo_ibge)
        )
        SELECT
            (SELECT count(*) FROM source),
            (SELECT count(*) FROM dim),
            (SELECT count(*) FROM matched),
            (SELECT list(codigo_ibge ORDER BY codigo_ibge)
             FROM source ANTI JOIN dim USING (codigo_ibge)),
            (SELECT list(codigo_ibge ORDER BY codigo_ibge)
             FROM dim ANTI JOIN source USING (codigo_ibge))
        """
    ).fetchone()
    source_count, dim_count, matched_count = matching[:3]
    unmatched_codes = matching[3] or []
    dim_without_record = matching[4] or []
    matching_report = {
        "source_municipalities": source_count,
        "dim_municipalities": dim_count,
        "matched_municipalities": matched_count,
        "unmatched_source_municipalities": len(unmatched_codes),
        "unmatched_source_codes": unmatched_codes,
        "dim_without_record_count": len(dim_without_record),
        "dim_without_record_codes": dim_without_record,
        "source_match_pct": matched_count / source_count * 100.0,
        "municipality_coverage_pct": matched_count / dim_count * 100.0,
    }
    _check(
        checks,
        name="source_municipalities_match_dim_municipality_by_code",
        observed={
            "source": source_count,
            "matched": matched_count,
            "unmatched": len(unmatched_codes),
        },
        expected={"source": source_count, "matched": source_count, "unmatched": 0},
        passed=matched_count == source_count and not unmatched_codes,
    )

    matched_fact_expected = int(
        _scalar(
            connection,
            "SELECT count(*) FROM silver_disaster_event WHERE is_dim_municipality_match",
        )
    )
    fact_duplicates = _duplicate_keys(
        connection, "fact_disaster_event", ("codigo_ibge", "disaster_event_id")
    )
    _check(
        checks,
        name="raw_silver_fact_rows_and_fact_grain_reconcile",
        observed={
            "raw": rows["raw"],
            "silver": rows["silver"],
            "fact": rows["fact"],
            "fact_duplicate_keys": fact_duplicates,
        },
        expected={
            "raw": rows["raw"],
            "silver": rows["raw"],
            "fact": rows["silver"],
            "fact_duplicate_keys": 0,
        },
        passed=(
            rows["raw"] == rows["silver"]
            and rows["fact"] == rows["silver"]
            and fact_duplicates == 0
        ),
    )

    snapshot_duplicates = _duplicate_keys(
        connection,
        "snapshot_municipality_disaster_history",
        ("codigo_ibge", "reference_date"),
    )
    type_summary_duplicates = _duplicate_keys(
        connection,
        "municipality_disaster_type_summary",
        ("codigo_ibge", "cobrade_code"),
    )
    month_duplicates = _duplicate_keys(
        connection,
        "municipality_disaster_month_profile",
        ("codigo_ibge", "month"),
    )
    gold_reconciliation = connection.execute(
        """
        SELECT
            (SELECT sum(event_count) FROM snapshot_municipality_disaster_history),
            (SELECT sum(event_count) FROM municipality_disaster_type_summary),
            (SELECT sum(event_count) FROM municipality_disaster_month_profile)
        """
    ).fetchone()
    _check(
        checks,
        name="gold_grains_and_event_counts_reconcile",
        observed={
            "snapshot_rows": rows["snapshot"],
            "month_profile_rows": rows["month_profile"],
            "duplicate_keys": {
                "snapshot": snapshot_duplicates,
                "type_summary": type_summary_duplicates,
                "month_profile": month_duplicates,
            },
            "event_count_sums": {
                "snapshot": gold_reconciliation[0],
                "type_summary": gold_reconciliation[1],
                "month_profile": gold_reconciliation[2],
            },
        },
        expected={
            "snapshot_rows": dim_count,
            "month_profile_rows": dim_count * 12,
            "all_duplicate_keys": 0,
            "snapshot_and_month_event_count_sums": matched_fact_expected,
            "type_summary_event_count_sum": rows["fact"],
        },
        passed=(
            rows["snapshot"] == dim_count
            and rows["month_profile"] == dim_count * 12
            and snapshot_duplicates == type_summary_duplicates == month_duplicates == 0
            and gold_reconciliation[0] == matched_fact_expected
            and gold_reconciliation[1] == rows["fact"]
            and gold_reconciliation[2] == matched_fact_expected
        ),
    )

    anomaly_counts = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE NOT is_protocol_format_valid),
            count(*) FILTER (WHERE NOT is_protocol_ibge_consistent),
            count(*) FILTER (WHERE NOT is_protocol_cobrade_consistent),
            count(*) FILTER (WHERE is_event_after_registration)
        FROM silver_disaster_event
        """
    ).fetchone()
    natural_key_duplicate_groups = int(
        _scalar(
            connection,
            """
            SELECT count(*) FROM (
                SELECT codigo_ibge, event_date, cobrade_code
                FROM silver_disaster_event
                GROUP BY ALL HAVING count(*) > 1
            )
            """,
        )
    )
    municipality_name_variant_codes = int(
        _scalar(
            connection,
            """
            SELECT count(*) FROM (
                SELECT codigo_ibge FROM silver_disaster_event
                GROUP BY codigo_ibge
                HAVING count(DISTINCT municipality_name_source) > 1
            )
            """,
        )
    )
    anomaly_report = {
        "invalid_protocol_format": anomaly_counts[0],
        "protocol_ibge_conflicts": anomaly_counts[1],
        "protocol_cobrade_conflicts": anomaly_counts[2],
        "event_after_registration": anomaly_counts[3],
        "natural_key_duplicate_groups": natural_key_duplicate_groups,
        "municipality_codes_with_name_variants": municipality_name_variant_codes,
    }

    status_counts = {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT status_source, count(*) FROM silver_disaster_event GROUP BY 1 ORDER BY 1"
        ).fetchall()
    }
    _check(
        checks,
        name="recognition_status_values_are_known",
        observed=status_counts,
        expected="only Registro and Reconhecido",
        passed=set(status_counts) == {"Registro", "Reconhecido"},
    )

    examples = [
        {
            "codigo_ibge": row[0],
            "municipio": row[1],
            "event_count": row[2],
            "rain_related_event_count": row[3],
            "first_event_date": row[4].isoformat() if row[4] else None,
            "latest_event_date": row[5].isoformat() if row[5] else None,
        }
        for row in connection.execute(
            f"""
            SELECT
                s.codigo_ibge, d.municipio, s.event_count,
                s.rain_related_event_count, s.first_event_date, s.latest_event_date
            FROM snapshot_municipality_disaster_history s
            JOIN read_parquet('{dim_path}') d USING (codigo_ibge)
            WHERE s.codigo_ibge IN ('3304557', '3550308', '4202404', '5300108')
            ORDER BY s.codigo_ibge
            """
        ).fetchall()
    ]

    failed = [check for check in checks if check["status"] == "FAIL"]
    warnings = []
    if any(anomaly_report.values()):
        warnings.append(
            "Anomalias de protocolo, data, chave natural e nomes territoriais da "
            "fonte foram preservadas e quantificadas; nenhum ID foi reescrito."
        )
    if dim_without_record:
        warnings.append(
            f"{len(dim_without_record)} unidades da dim_municipality nao possuem "
            "registro Atlas; isso significa 0 eventos encontrados na fonte."
        )
    unused_cobrade = [
        row[0]
        for row in connection.execute(
            """
            SELECT d.cobrade_code
            FROM dim_disaster_type d
            ANTI JOIN (SELECT DISTINCT cobrade_code FROM silver_disaster_event) s
                USING (cobrade_code)
            ORDER BY d.cobrade_code
            """
        ).fetchall()
    ]
    if unused_cobrade:
        warnings.append(
            "A dimensao oficial contem codigos COBRADE sem eventos nesta release: "
            + ", ".join(unused_cobrade)
            + "."
        )

    return {
        "status": "PASS" if not failed else "FAIL",
        "generated_at": generated_at.isoformat(),
        "source": "Atlas Digital de Desastres no Brasil / S2ID",
        "source_release": source_release,
        "source_official_date": source_official_date,
        "source_inspection": asdict(inspection),
        "source_urls": {
            name: manifest["discovered_download_url"]
            for name, manifest in resources.items()
        },
        "resolved_urls": {
            name: manifest["resolved_download_url"]
            for name, manifest in resources.items()
        },
        "source_hashes": {
            name: manifest["sha256"] for name, manifest in resources.items()
        },
        "rows": rows,
        "matching": matching_report,
        "status_counts": status_counts,
        "anomalies_preserved": anomaly_report,
        "unused_cobrade_codes": unused_cobrade,
        "checks": checks,
        "problems_found": [check["name"] for check in failed],
        "warnings": warnings,
        "examples": examples,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def write_atlas_quality_reports(
    report: dict[str, Any], *, json_path: Path, markdown_path: Path
) -> None:
    _atomic_write(
        json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    checks = "\n".join(
        f"| `{check['name']}` | {check['status']} | "
        f"`{json.dumps(check['observed'], ensure_ascii=False)}` | "
        f"`{json.dumps(check['expected'], ensure_ascii=False)}` |"
        for check in report["checks"]
    )
    warnings = "\n".join(f"- {warning}" for warning in report["warnings"])
    warnings = warnings or "- Nenhuma ressalva."
    problems = "\n".join(f"- `{name}`" for name in report["problems_found"])
    problems = problems or "Nenhum problema de qualidade encontrado."
    matching = report["matching"]
    rows = report["rows"]
    markdown = f"""# Atlas/S2ID Data Quality Report

- Status: **{report['status']}**
- Gerado em: `{report['generated_at']}`
- Release: `{report['source_release']}`
- Data oficial da release: `{report['source_official_date']}`
- Eventos RAW/SILVER/FACT: **{rows['raw']} / {rows['silver']} / {rows['fact']}**
- Tipos COBRADE: **{rows['disaster_type']}**
- Snapshots municipais: **{rows['snapshot']}**

## Matching Municipal

- Municipios distintos na fonte: **{matching['source_municipalities']}**
- Municipios associados: **{matching['matched_municipalities']}**
- Fonte sem correspondencia: **{matching['unmatched_source_municipalities']}**
- Cobertura da `dim_municipality`: **{matching['municipality_coverage_pct']:.6f}%**
- Dimensao sem registro Atlas: **{matching['dim_without_record_count']}**

Ausencia de registro significa somente **0 eventos encontrados na fonte**; nao
significa que nenhum desastre ocorreu.

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
{checks}

## Problemas Encontrados

{problems}

## Ressalvas

{warnings}

## Anomalias Preservadas

```json
{json.dumps(report['anomalies_preserved'], ensure_ascii=False, indent=2)}
```

Os dados descrevem registros oficiais historicos. Nao representam risco futuro,
probabilidade de desastre, causalidade ou ausencia do fenomeno.
"""
    _atomic_write(markdown_path, markdown)
