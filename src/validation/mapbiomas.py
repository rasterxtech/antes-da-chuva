from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from src.transform.mapbiomas import ClassSemantics, SourceInspection


MUNICIPALITY_COVERAGE_FAILURE_THRESHOLD_PCT = 99.0
MAPPED_AREA_VARIATION_WARNING_THRESHOLD_PCT = 0.1
MAPPED_AREA_VARIATION_FAILURE_THRESHOLD_PCT = 1.0
PERCENTAGE_TOLERANCE = 1e-9
EXAMPLE_CODES = ("3304557", "3550308", "4202404", "5300108")


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


def _null_counts(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    columns: tuple[str, ...],
) -> dict[str, int]:
    return {
        column: int(
            _scalar(
                connection,
                f'SELECT count(*) FILTER (WHERE "{column}" IS NULL) FROM {table}',
            )
        )
        for column in columns
    }


def validate_mapbiomas(
    connection: duckdb.DuckDBPyConnection,
    *,
    inspection: SourceInspection,
    semantics: ClassSemantics,
    collection_id: str,
    collection_version: str,
    statistics_manifest: dict[str, Any],
    legend_manifest: dict[str, Any],
    dim_municipality_path: Path,
    generated_at: datetime,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    rows_raw = int(_scalar(connection, "SELECT count(*) FROM raw_mapbiomas_wide"))
    rows_silver = int(
        _scalar(connection, "SELECT count(*) FROM silver_mapbiomas_land_cover")
    )
    rows_fact = int(
        _scalar(connection, "SELECT count(*) FROM fact_municipality_land_cover")
    )
    rows_snapshot = int(
        _scalar(connection, "SELECT count(*) FROM snapshot_municipality_land_cover")
    )
    rows_change = int(
        _scalar(connection, "SELECT count(*) FROM municipality_land_cover_change")
    )

    _check(
        checks,
        name="raw_files_are_nonempty_and_readable",
        observed={
            "statistics_bytes": statistics_manifest["content_length"],
            "legend_bytes": legend_manifest["content_length"],
            "xlsx_rows": rows_raw,
        },
        expected={"statistics_bytes": "> 0", "legend_bytes": "> 0", "xlsx_rows": "> 0"},
        passed=(
            statistics_manifest["content_length"] > 0
            and legend_manifest["content_length"] > 0
            and rows_raw > 0
        ),
    )

    observed_years = [
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT year FROM silver_mapbiomas_land_cover ORDER BY year"
        ).fetchall()
    ]
    expected_years = list(range(inspection.first_year, inspection.latest_year + 1))
    _check(
        checks,
        name="annual_series_is_complete",
        observed={
            "min_year": min(observed_years),
            "max_year": max(observed_years),
            "year_count": len(observed_years),
            "gaps": sorted(set(expected_years) - set(observed_years)),
        },
        expected={
            "min_year": inspection.first_year,
            "max_year": inspection.latest_year,
            "year_count": inspection.year_count,
            "gaps": [],
        },
        passed=observed_years == expected_years,
    )

    required_silver = (
        "collection_id",
        "collection_version",
        "codigo_ibge",
        "biome_name",
        "year",
        "class_id",
        "class_name",
        "class_level",
        "area_ha",
    )
    silver_nulls = _null_counts(
        connection, "silver_mapbiomas_land_cover", required_silver
    )
    negative_areas = int(
        _scalar(
            connection,
            "SELECT count(*) FROM silver_mapbiomas_land_cover WHERE area_ha < 0",
        )
    )
    _check(
        checks,
        name="silver_required_fields_and_nonnegative_area",
        observed={"nulls": silver_nulls, "negative_area_rows": negative_areas},
        expected={
            "nulls": {column: 0 for column in required_silver},
            "negative_area_rows": 0,
        },
        passed=all(value == 0 for value in silver_nulls.values())
        and negative_areas == 0,
    )

    expected_silver_rows = int(
        _scalar(
            connection,
            f"""
            SELECT count(*) * {inspection.year_count}
            FROM (
                SELECT geocode, biome, "class"
                FROM raw_mapbiomas_wide
                GROUP BY ALL
            )
            """,
        )
    )
    silver_duplicates = int(
        _scalar(
            connection,
            """
            SELECT count(*) FROM (
                SELECT collection_id, codigo_ibge, biome_name, year, class_id
                FROM silver_mapbiomas_land_cover
                GROUP BY ALL HAVING count(*) > 1
            )
            """,
        )
    )
    _check(
        checks,
        name="silver_grain_is_unique_and_reconciled",
        observed={"rows": rows_silver, "duplicate_keys": silver_duplicates},
        expected={"rows": expected_silver_rows, "duplicate_keys": 0},
        passed=rows_silver == expected_silver_rows and silver_duplicates == 0,
    )

    matching = connection.execute(
        f"""
        WITH mapbiomas AS (
            SELECT DISTINCT codigo_ibge
            FROM silver_mapbiomas_land_cover
        ), dim AS (
            SELECT codigo_ibge
            FROM read_parquet('{str(dim_municipality_path).replace("'", "''")}')
        ), matched AS (
            SELECT codigo_ibge FROM mapbiomas INNER JOIN dim USING (codigo_ibge)
        )
        SELECT
            (SELECT count(*) FROM mapbiomas),
            (SELECT count(*) FROM dim),
            (SELECT count(*) FROM matched),
            (SELECT list(codigo_ibge ORDER BY codigo_ibge)
             FROM mapbiomas ANTI JOIN dim USING (codigo_ibge)),
            (SELECT list(codigo_ibge ORDER BY codigo_ibge)
             FROM dim ANTI JOIN mapbiomas USING (codigo_ibge))
        """
    ).fetchone()
    mapbiomas_municipalities, dim_municipalities, matched = matching[:3]
    mapbiomas_without_dim = matching[3] or []
    dim_without_mapbiomas = matching[4] or []
    coverage_pct = matched / dim_municipalities * 100.0
    matching_report = {
        "municipios_mapbiomas": mapbiomas_municipalities,
        "municipios_dim_municipality": dim_municipalities,
        "municipios_matched": matched,
        "municipios_unmatched": len(mapbiomas_without_dim),
        "codigo_mapbiomas_sem_dim": mapbiomas_without_dim,
        "codigo_dim_sem_mapbiomas": dim_without_mapbiomas,
        "coverage_pct": coverage_pct,
    }
    _check(
        checks,
        name="municipality_dimension_coverage",
        observed=matching_report,
        expected={
            "coverage_pct": f">= {MUNICIPALITY_COVERAGE_FAILURE_THRESHOLD_PCT}",
        },
        passed=coverage_pct >= MUNICIPALITY_COVERAGE_FAILURE_THRESHOLD_PCT,
    )

    fact_duplicates = int(
        _scalar(
            connection,
            """
            SELECT count(*) FROM (
                SELECT codigo_ibge, year, class_id
                FROM fact_municipality_land_cover
                GROUP BY ALL HAVING count(*) > 1
            )
            """,
        )
    )
    biome_aggregation_differences = int(
        _scalar(
            connection,
            """
            WITH silver_sum AS (
                SELECT codigo_ibge, year, class_id, sum(area_ha) area_ha
                FROM silver_mapbiomas_land_cover
                WHERE is_dim_municipality_match
                GROUP BY ALL
            )
            SELECT count(*)
            FROM silver_sum s
            FULL JOIN fact_municipality_land_cover f
                USING (codigo_ibge, year, class_id)
            WHERE abs(coalesce(s.area_ha, 0) - coalesce(f.area_ha, 0)) > 1e-8
            """,
        )
    )
    _check(
        checks,
        name="fact_grain_and_biome_sum_are_correct",
        observed={
            "duplicate_keys": fact_duplicates,
            "aggregation_differences": biome_aggregation_differences,
        },
        expected={"duplicate_keys": 0, "aggregation_differences": 0},
        passed=fact_duplicates == 0 and biome_aggregation_differences == 0,
    )

    source_class_ids = set(inspection.classes_in_statistics)
    semantic_class_ids = {
        semantics.urban_class_id,
        semantics.water_class_id,
        semantics.wetland_class_id,
        *semantics.native_vegetation_class_ids,
        *semantics.agriculture_livestock_class_ids,
    }
    _check(
        checks,
        name="indicator_classes_come_from_official_hierarchy",
        observed={
            "urban": semantics.urban_class_id,
            "water": semantics.water_class_id,
            "wetland": semantics.wetland_class_id,
            "native_vegetation": list(semantics.native_vegetation_class_ids),
            "agriculture_livestock": list(
                semantics.agriculture_livestock_class_ids
            ),
        },
        expected="all IDs present in the official statistics hierarchy",
        passed=semantic_class_ids <= source_class_ids,
    )

    mapped_area_variations = connection.execute(
        f"""
        WITH variation AS (
            SELECT
                codigo_ibge,
                min(mapped_area_ha) AS min_mapped_area_ha,
                max(mapped_area_ha) AS max_mapped_area_ha,
                avg(mapped_area_ha) AS avg_mapped_area_ha,
                (max(mapped_area_ha) - min(mapped_area_ha))
                    / nullif(avg(mapped_area_ha), 0) * 100.0
                    AS variation_pct
            FROM snapshot_municipality_land_cover
            GROUP BY codigo_ibge
        )
        SELECT
            count(*) FILTER (WHERE min_mapped_area_ha <= 0),
            count(*) FILTER (
                WHERE variation_pct > {MAPPED_AREA_VARIATION_WARNING_THRESHOLD_PCT}
            ),
            count(*) FILTER (
                WHERE variation_pct > {MAPPED_AREA_VARIATION_FAILURE_THRESHOLD_PCT}
            ),
            max(variation_pct),
            quantile_cont(variation_pct, [0.5, 0.9, 0.95, 0.99])
        FROM variation
        """
    ).fetchone()
    nonpositive_mapped, area_warnings, area_failures, max_variation, quantiles = (
        mapped_area_variations
    )
    _check(
        checks,
        name="mapped_municipality_area_is_positive_and_stable",
        observed={
            "nonpositive_rows": nonpositive_mapped,
            "over_warning_threshold": area_warnings,
            "over_failure_threshold": area_failures,
            "max_variation_pct": max_variation,
            "variation_quantiles_pct": {
                "p50": quantiles[0],
                "p90": quantiles[1],
                "p95": quantiles[2],
                "p99": quantiles[3],
            },
        },
        expected={
            "nonpositive_rows": 0,
            "over_failure_threshold": 0,
            "failure_threshold_pct": MAPPED_AREA_VARIATION_FAILURE_THRESHOLD_PCT,
        },
        passed=nonpositive_mapped == 0 and area_failures == 0,
    )
    largest_area_variations = [
        {
            "codigo_ibge": row[0],
            "municipio": row[1],
            "min_mapped_area_ha": row[2],
            "max_mapped_area_ha": row[3],
            "variation_pct": row[4],
        }
        for row in connection.execute(
            f"""
            WITH variation AS (
                SELECT
                    s.codigo_ibge,
                    min(s.mapped_area_ha) AS min_area,
                    max(s.mapped_area_ha) AS max_area,
                    (max(s.mapped_area_ha) - min(s.mapped_area_ha))
                        / nullif(avg(s.mapped_area_ha), 0) * 100.0 AS variation_pct
                FROM snapshot_municipality_land_cover s
                GROUP BY s.codigo_ibge
            )
            SELECT v.codigo_ibge, d.municipio, v.min_area, v.max_area,
                   v.variation_pct
            FROM variation v
            JOIN read_parquet('{str(dim_municipality_path).replace("'", "''")}') d
                USING (codigo_ibge)
            ORDER BY variation_pct DESC
            LIMIT 20
            """
        ).fetchall()
    ]

    percentage_columns = (
        "urban_area_pct",
        "native_vegetation_area_pct",
        "agriculture_livestock_area_pct",
        "water_area_pct",
        "wetland_area_pct",
    )
    invalid_percentages = {
        column: int(
            _scalar(
                connection,
                f"""
                SELECT count(*) FROM snapshot_municipality_land_cover
                WHERE {column} < -{PERCENTAGE_TOLERANCE}
                   OR {column} > {100 + PERCENTAGE_TOLERANCE}
                """,
            )
        )
        for column in percentage_columns
    }
    _check(
        checks,
        name="snapshot_percentages_are_bounded",
        observed=invalid_percentages,
        expected={column: 0 for column in percentage_columns},
        passed=all(count == 0 for count in invalid_percentages.values()),
    )

    examples = [
        {
            "codigo_ibge": row[0],
            "municipio": row[1],
            "first_year": row[2],
            "latest_year": row[3],
            "urban_area_ha": row[4],
            "urban_area_pct": row[5],
            "native_vegetation_area_ha": row[6],
            "native_vegetation_area_pct": row[7],
            "water_area_ha": row[8],
            "wetland_area_ha": row[9],
            "urban_area_change_ha": row[10],
            "urban_area_change_pct": row[11],
            "native_vegetation_change_ha": row[12],
            "native_vegetation_change_pct": row[13],
        }
        for row in connection.execute(
            f"""
            SELECT
                s.codigo_ibge,
                d.municipio,
                c.first_year,
                c.latest_year,
                s.urban_area_ha,
                s.urban_area_pct,
                s.native_vegetation_area_ha,
                s.native_vegetation_area_pct,
                s.water_area_ha,
                s.wetland_area_ha,
                c.urban_area_change_ha,
                c.urban_area_change_pct,
                c.native_vegetation_change_ha,
                c.native_vegetation_change_pct
            FROM snapshot_municipality_land_cover s
            JOIN municipality_land_cover_change c USING (codigo_ibge)
            JOIN read_parquet('{str(dim_municipality_path).replace("'", "''")}') d
                USING (codigo_ibge)
            WHERE s.year = c.latest_year
              AND s.codigo_ibge IN ({', '.join('?' for _ in EXAMPLE_CODES)})
            ORDER BY s.codigo_ibge
            """,
            list(EXAMPLE_CODES),
        ).fetchall()
    ]
    _check(
        checks,
        name="required_municipality_examples_are_present",
        observed=len(examples),
        expected=len(EXAMPLE_CODES),
        passed=len(examples) == len(EXAMPLE_CODES),
    )

    source_duplicate_details = [
        {
            "codigo_ibge": row[0],
            "municipality": row[1],
            "biome": row[2],
            "class_id": row[3],
            "source_rows": row[4],
            "states": row[5],
        }
        for row in connection.execute(
            """
            SELECT
                geocode,
                any_value(municipality),
                biome,
                CAST("class" AS INTEGER),
                count(*),
                list_sort(list_distinct(list(state)))
            FROM raw_mapbiomas_wide
            GROUP BY geocode, biome, "class"
            HAVING count(*) > 1
            ORDER BY geocode, biome, "class"
            """
        ).fetchall()
    ]
    failed_checks = [check for check in checks if check["status"] == "FAIL"]
    warnings = []
    if inspection.classes_statistics_only or inspection.classes_legend_only:
        warnings.append(
            "O XLSX e o CSV oficial de legenda possuem conjuntos de classes "
            "diferentes; classes exclusivas do XLSX usam a hierarquia do workbook."
        )
    if mapbiomas_without_dim or dim_without_mapbiomas:
        warnings.append(
            "A cobertura municipal nao e exatamente igual a dim_municipality; "
            "os codigos divergentes permanecem explicitos no matching report."
        )
    if source_duplicate_details:
        warnings.append(
            "A fonte possui grao duplicado; a SILVER consolida por soma e preserva "
            "source_row_count e as listas de estados/regioes originais."
        )
    if area_warnings:
        warnings.append(
            f"{area_warnings} municipio(s) excedem {MAPPED_AREA_VARIATION_WARNING_THRESHOLD_PCT}% "
            "de variacao da area mapeada entre anos, sem exceder o limite de falha."
        )

    return {
        "status": "PASS" if not failed_checks else "FAIL",
        "generated_at": generated_at.isoformat(),
        "collection_id": collection_id,
        "collection_version": collection_version,
        "source_publication_date": statistics_manifest["source_publication_date"],
        "source_urls": {
            "statistics_discovery": statistics_manifest["discovery_url"],
            "statistics_download": statistics_manifest["discovered_download_url"],
            "legend_discovery": legend_manifest["discovery_url"],
            "legend_download": legend_manifest["discovered_download_url"],
        },
        "source_hashes": {
            "statistics": statistics_manifest["sha256"],
            "statistics_xlsx_member": statistics_manifest["extracted_sha256"],
            "legend": legend_manifest["sha256"],
        },
        "source_inspection": asdict(inspection),
        "class_semantics": asdict(semantics),
        "rows": {
            "raw_wide": rows_raw,
            "silver": rows_silver,
            "fact": rows_fact,
            "snapshot": rows_snapshot,
            "change": rows_change,
        },
        "matching": matching_report,
        "checks": checks,
        "problems_found": [check["name"] for check in failed_checks],
        "warnings": warnings,
        "source_duplicate_details": source_duplicate_details,
        "largest_mapped_area_variations": largest_area_variations,
        "examples": examples,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)


def write_mapbiomas_quality_reports(
    report: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )
    check_rows = "\n".join(
        f"| `{check['name']}` | {check['status']} | "
        f"`{json.dumps(check['observed'], ensure_ascii=False)}` | "
        f"`{json.dumps(check['expected'], ensure_ascii=False)}` |"
        for check in report["checks"]
    )
    warning_rows = (
        "\n".join(f"- {warning}" for warning in report["warnings"])
        or "- Nenhuma ressalva."
    )
    problem_rows = (
        "\n".join(f"- `{problem}`" for problem in report["problems_found"])
        or "Nenhum problema de qualidade encontrado."
    )
    example_rows = "\n".join(
        "| {codigo_ibge} | {municipio} | {first_year} | {latest_year} | "
        "{urban_area_ha:.3f} | {urban_area_pct:.3f} | "
        "{native_vegetation_area_ha:.3f} | {native_vegetation_area_pct:.3f} | "
        "{water_area_ha:.3f} | {wetland_area_ha:.3f} | "
        "{urban_area_change_ha:.3f} | {native_vegetation_change_ha:.3f} |".format(
            **example
        )
        for example in report["examples"]
    )
    matching = report["matching"]
    semantics = report["class_semantics"]
    markdown = f"""# MapBiomas Data Quality Report

- Status: **{report['status']}**
- Gerado em: `{report['generated_at']}`
- Colecao: `{report['collection_id']}`
- Versao: `{report['collection_version']}`
- Publicacao: `{report['source_publication_date']}`
- Serie: `{report['source_inspection']['first_year']}–{report['source_inspection']['latest_year']}`
- RAW: **{report['rows']['raw_wide']}** linhas largas
- SILVER: **{report['rows']['silver']}** linhas
- FACT: **{report['rows']['fact']}** linhas
- SNAPSHOT: **{report['rows']['snapshot']}** linhas
- CHANGE: **{report['rows']['change']}** linhas

## Matching Municipal

- MapBiomas: **{matching['municipios_mapbiomas']}** codigos
- `dim_municipality`: **{matching['municipios_dim_municipality']}** codigos
- Matched: **{matching['municipios_matched']}**
- Cobertura da dimensao: **{matching['coverage_pct']:.6f}%**
- MapBiomas sem dimensao: `{matching['codigo_mapbiomas_sem_dim']}`
- Dimensao sem MapBiomas: `{matching['codigo_dim_sem_mapbiomas']}`

## Classes dos Indicadores

- Area urbanizada: `{semantics['urban_class_id']}`
- Agua: `{semantics['water_class_id']}`
- Campo alagado/area pantanosa: `{semantics['wetland_class_id']}`
- Vegetacao nativa: `{semantics['native_vegetation_class_ids']}`
- Agropecuaria: `{semantics['agriculture_livestock_class_ids']}`
- Classes mapeadas no denominador: `{semantics['mapped_class_ids']}`
- Classes excluidas como nao observadas: `{semantics['not_observed_class_ids']}`

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
{check_rows}

## Problemas Encontrados

{problem_rows}

## Ressalvas

{warning_rows}

## Exemplos no Ultimo Ano

| codigo_ibge | municipio | primeiro ano | ultimo ano | urbano ha | urbano % | vegetacao nativa ha | vegetacao nativa % | agua ha | area umida ha | mudanca urbana ha | mudanca vegetacao ha |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{example_rows}

Os indicadores descrevem cobertura observada. Nao representam risco, causalidade,
impermeabilizacao, disponibilidade hidrica ou vulnerabilidade.
"""
    _atomic_write(markdown_path, markdown)
