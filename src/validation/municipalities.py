from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb


REQUIRED_NOT_NULL = (
    "codigo_ibge",
    "municipio",
    "sigla_uf",
    "codigo_uf_ibge",
    "regiao",
)

EXPECTED_EXAMPLES = (
    "2605459",
    "3304557",
    "3550308",
    "4202404",
    "5300108",
)


def _scalar(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


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


def validate_dimension(
    connection: duckdb.DuckDBPyConnection,
    *,
    official_source_codes: set[str],
    generated_at: datetime,
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    table = "dim_municipality"
    checks: list[dict[str, Any]] = []
    row_count = _scalar(connection, f"SELECT count(*) FROM {table}")
    distinct_codes = _scalar(
        connection, f"SELECT count(DISTINCT codigo_ibge) FROM {table}"
    )
    duplicate_codes = _scalar(
        connection,
        f"""
        SELECT count(*) FROM (
            SELECT codigo_ibge FROM {table}
            GROUP BY codigo_ibge HAVING count(*) > 1
        )
        """,
    )

    _check(
        checks,
        name="record_count_matches_official_api_response",
        observed=row_count,
        expected=source_metadata["record_count"],
        passed=row_count == source_metadata["record_count"],
    )
    _check(
        checks,
        name="codigo_ibge_is_unique",
        observed=duplicate_codes,
        expected=0,
        passed=duplicate_codes == 0 and distinct_codes == row_count,
    )

    columns = [
        row[0]
        for row in connection.execute(f"DESCRIBE {table}").fetchall()
    ]
    null_counts = {
        column: _scalar(
            connection,
            f'SELECT count(*) FILTER (WHERE "{column}" IS NULL) FROM {table}',
        )
        for column in columns
    }
    required_nulls = {column: null_counts[column] for column in REQUIRED_NOT_NULL}
    _check(
        checks,
        name="required_fields_are_not_null",
        observed=required_nulls,
        expected={column: 0 for column in REQUIRED_NOT_NULL},
        passed=all(count == 0 for count in required_nulls.values()),
    )

    source_codes = {
        row[0]
        for row in connection.execute(f"SELECT codigo_ibge FROM {table}").fetchall()
    }
    missing_codes = sorted(official_source_codes - source_codes)
    unexpected_codes = sorted(source_codes - official_source_codes)
    _check(
        checks,
        name="codigo_ibge_set_matches_official_api_response",
        observed={
            "missing_count": len(missing_codes),
            "unexpected_count": len(unexpected_codes),
        },
        expected={"missing_count": 0, "unexpected_count": 0},
        passed=not missing_codes and not unexpected_codes,
    )

    invalid_municipality_codes = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE NOT regexp_full_match(codigo_ibge, '[0-9]{{7}}')",
    )
    invalid_uf_codes = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE NOT regexp_full_match(codigo_uf_ibge, '[0-9]{{2}}')",
    )
    invalid_region_codes = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE NOT regexp_full_match(codigo_regiao, '[1-5]')",
    )
    invalid_immediate_region_codes = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE NOT regexp_full_match(codigo_regiao_imediata, '[0-9]{{6}}')",
    )
    invalid_intermediate_region_codes = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE NOT regexp_full_match(codigo_regiao_intermediaria, '[0-9]{{4}}')",
    )
    municipality_uf_prefix_conflicts = _scalar(
        connection,
        f"SELECT count(*) FROM {table} WHERE left(codigo_ibge, 2) <> codigo_uf_ibge",
    )
    _check(
        checks,
        name="administrative_code_formats_are_valid",
        observed={
            "invalid_codigo_ibge": invalid_municipality_codes,
            "invalid_codigo_uf_ibge": invalid_uf_codes,
            "invalid_codigo_regiao": invalid_region_codes,
            "invalid_codigo_regiao_imediata": invalid_immediate_region_codes,
            "invalid_codigo_regiao_intermediaria": invalid_intermediate_region_codes,
            "municipality_uf_prefix_conflicts": municipality_uf_prefix_conflicts,
        },
        expected={
            "invalid_codigo_ibge": 0,
            "invalid_codigo_uf_ibge": 0,
            "invalid_codigo_regiao": 0,
            "invalid_codigo_regiao_imediata": 0,
            "invalid_codigo_regiao_intermediaria": 0,
            "municipality_uf_prefix_conflicts": 0,
        },
        passed=all(
            count == 0
            for count in (
                invalid_municipality_codes,
                invalid_uf_codes,
                invalid_region_codes,
                invalid_immediate_region_codes,
                invalid_intermediate_region_codes,
                municipality_uf_prefix_conflicts,
            )
        ),
    )

    municipalities_with_invalid_uf_cardinality = _scalar(
        connection,
        f"""
        SELECT count(*) FROM (
            SELECT codigo_ibge
            FROM {table}
            GROUP BY codigo_ibge
            HAVING count(DISTINCT codigo_uf_ibge) <> 1
        )
        """,
    )
    _check(
        checks,
        name="each_municipality_belongs_to_exactly_one_uf",
        observed=municipalities_with_invalid_uf_cardinality,
        expected=0,
        passed=municipalities_with_invalid_uf_cardinality == 0,
    )

    ufs_with_invalid_region_cardinality = _scalar(
        connection,
        f"""
        SELECT count(*) FROM (
            SELECT codigo_uf_ibge
            FROM {table}
            GROUP BY codigo_uf_ibge
            HAVING count(DISTINCT codigo_regiao) <> 1
        )
        """,
    )
    _check(
        checks,
        name="each_uf_belongs_to_exactly_one_region",
        observed=ufs_with_invalid_region_cardinality,
        expected=0,
        passed=ufs_with_invalid_region_cardinality == 0,
    )

    hierarchy_nulls = {
        column: null_counts[column]
        for column in (
            "regiao_imediata",
            "codigo_regiao_imediata",
            "regiao_intermediaria",
            "codigo_regiao_intermediaria",
        )
    }
    _check(
        checks,
        name="current_geographic_regions_are_complete",
        observed=hierarchy_nulls,
        expected={column: 0 for column in hierarchy_nulls},
        passed=all(count == 0 for count in hierarchy_nulls.values()),
    )

    example_rows = connection.execute(
        f"""
        SELECT codigo_ibge, municipio, sigla_uf, regiao,
               regiao_imediata, regiao_intermediaria
        FROM {table}
        WHERE codigo_ibge IN ({', '.join('?' for _ in EXPECTED_EXAMPLES)})
        ORDER BY codigo_ibge
        """,
        list(EXPECTED_EXAMPLES),
    ).fetchall()
    examples = [
        dict(
            zip(
                (
                    "codigo_ibge",
                    "municipio",
                    "sigla_uf",
                    "regiao",
                    "regiao_imediata",
                    "regiao_intermediaria",
                ),
                row,
            )
        )
        for row in example_rows
    ]
    _check(
        checks,
        name="required_documentation_examples_are_present",
        observed=len(examples),
        expected=len(EXPECTED_EXAMPLES),
        passed=len(examples) == len(EXPECTED_EXAMPLES),
    )

    special_type_conflicts = _scalar(
        connection,
        f"""
        SELECT count(*) FROM {table}
        WHERE (codigo_ibge = '2605459' AND tipo_unidade_territorial <> 'distrito_estadual')
           OR (codigo_ibge = '5300108' AND tipo_unidade_territorial <> 'distrito_federal')
        """,
    )
    _check(
        checks,
        name="special_territorial_units_are_classified",
        observed=special_type_conflicts,
        expected=0,
        passed=special_type_conflicts == 0,
    )

    territorial_type_counts = {
        territorial_type: count
        for territorial_type, count in connection.execute(
            f"""
            SELECT tipo_unidade_territorial, count(*)
            FROM {table}
            GROUP BY tipo_unidade_territorial
            ORDER BY tipo_unidade_territorial
            """
        ).fetchall()
    }
    number_of_ufs = _scalar(
        connection, f"SELECT count(DISTINCT codigo_uf_ibge) FROM {table}"
    )
    number_of_regions = _scalar(
        connection, f"SELECT count(DISTINCT codigo_regiao) FROM {table}"
    )

    failed_checks = [check for check in checks if check["status"] == "FAIL"]
    warnings = []
    if null_counts["source_updated_at"] == row_count:
        warnings.append(
            "source_updated_at esta nulo porque a API nao informa versao, data de "
            "referencia, Last-Modified ou ETag."
        )
    warnings.extend(
        (
            "A rota de municipios inclui Brasilia (Distrito Federal) e Fernando de "
            "Noronha (distrito estadual) no nivel analitico municipal.",
            "Mesorregiao e microrregiao foram mantidas apenas na SILVER; a "
            "microrregiao e nula para Boa Esperanca do Norte na fonte atual.",
        )
    )

    return {
        "status": "PASS" if not failed_checks else "FAIL",
        "generated_at": generated_at.isoformat(),
        "source": source_metadata["source"],
        "source_url": source_metadata["source_url"],
        "source_query_date": source_metadata["queried_at"][:10],
        "source_updated_at": source_metadata["source_updated_at"],
        "official_source_record_count": source_metadata["record_count"],
        "number_of_rows": row_count,
        "number_of_municipalities_stricto_sensu": territorial_type_counts.get(
            "municipio", 0
        ),
        "number_of_ufs": number_of_ufs,
        "number_of_regions": number_of_regions,
        "duplicate_codigo_ibge": duplicate_codes,
        "null_counts": null_counts,
        "territorial_type_counts": territorial_type_counts,
        "checks": checks,
        "problems_found": [check["name"] for check in failed_checks],
        "warnings": warnings,
        "missing_codigo_ibge": missing_codes,
        "unexpected_codigo_ibge": unexpected_codes,
        "examples": examples,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)


def write_quality_reports(
    report: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )

    null_rows = "\n".join(
        f"| `{column}` | {count} |"
        for column, count in report["null_counts"].items()
    )
    check_rows = "\n".join(
        f"| `{check['name']}` | {check['status']} | "
        f"`{json.dumps(check['observed'], ensure_ascii=False)}` | "
        f"`{json.dumps(check['expected'], ensure_ascii=False)}` |"
        for check in report["checks"]
    )
    example_rows = "\n".join(
        "| {codigo_ibge} | {municipio} | {sigla_uf} | {regiao} | "
        "{regiao_imediata} | {regiao_intermediaria} |".format(**example)
        for example in report["examples"]
    )
    warnings = "\n".join(f"- {warning}" for warning in report["warnings"])
    problems = (
        "\n".join(f"- `{problem}`" for problem in report["problems_found"])
        if report["problems_found"]
        else "Nenhum problema de qualidade encontrado."
    )
    territorial_types = ", ".join(
        f"`{key}`: {value}"
        for key, value in report["territorial_type_counts"].items()
    )

    markdown = f"""# Data Quality Report

- Status: **{report['status']}**
- Gerado em: `{report['generated_at']}`
- Consulta da fonte: `{report['source_query_date']}`
- Registros oficiais retornados pela API: **{report['official_source_record_count']}**
- Localidades no nivel municipal em `dim_municipality`: **{report['number_of_rows']}**
- Municipios stricto sensu: **{report['number_of_municipalities_stricto_sensu']}**
- UFs: **{report['number_of_ufs']}**
- Regioes: **{report['number_of_regions']}**
- Duplicados de `codigo_ibge`: **{report['duplicate_codigo_ibge']}**
- Tipos territoriais: {territorial_types}

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
{check_rows}

## Nulls

| Coluna | Nulls |
|---|---:|
{null_rows}

`source_updated_at` nulo e esperado: a API nao fornece essa metadata.

## Problemas Encontrados

{problems}

## Ressalvas

{warnings}

## Exemplos

| codigo_ibge | municipio | UF | regiao | regiao_imediata | regiao_intermediaria |
|---|---|---|---|---|---|
{example_rows}

O relatorio estruturado esta em `data/gold/data_quality_report.json`.
"""
    _atomic_write(markdown_path, markdown)
