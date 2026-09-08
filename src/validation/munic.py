from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from src.contracts.munic import GOLD_STATUSES, OUTPUT_STATUS_FIELDS, SOURCE_STATUSES


def _check(checks: list[dict[str, Any]], name: str, observed: Any, expected: Any) -> None:
    checks.append(
        {
            "name": name,
            "status": "PASS" if observed == expected else "FAIL",
            "observed": observed,
            "expected": expected,
        }
    )


def validate_munic(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_metadata: dict,
    generated_at: str,
) -> dict:
    checks: list[dict[str, Any]] = []
    source_rows = connection.execute("SELECT count(*) FROM silver_munic").fetchone()[0]
    gold_rows = connection.execute("SELECT count(*) FROM gold_munic").fetchone()[0]
    duplicates = connection.execute(
        "SELECT count(*) FROM (SELECT codigo_ibge FROM silver_munic GROUP BY ALL HAVING count(*) > 1)"
    ).fetchone()[0]
    invalid_codes = connection.execute(
        "SELECT count(*) FROM silver_munic WHERE NOT regexp_matches(codigo_ibge, '^[0-9]{7}$')"
    ).fetchone()[0]
    source_without_dimension = connection.execute(
        "SELECT count(*) FROM silver_munic s ANTI JOIN gold_munic g USING (codigo_ibge)"
    ).fetchone()[0]
    not_in_source = connection.execute(
        "SELECT list(codigo_ibge ORDER BY codigo_ibge) FROM gold_munic WHERE NOT in_source"
    ).fetchone()[0] or []

    _check(checks, "source_has_5570_municipalities", source_rows, 5570)
    _check(checks, "source_codigo_ibge_is_unique", duplicates, 0)
    _check(checks, "source_codigo_ibge_format_is_valid", invalid_codes, 0)
    _check(checks, "all_source_codes_match_current_dimension", source_without_dimension, 0)
    _check(checks, "gold_matches_current_dimension", gold_rows, 5571)
    _check(checks, "new_municipality_is_explicitly_outside_2020_source", not_in_source, ["5101837"])

    invalid_statuses: dict[str, int] = {}
    for field in OUTPUT_STATUS_FIELDS:
        allowed = GOLD_STATUSES if field else SOURCE_STATUSES
        values = ", ".join(f"'{value}'" for value in sorted(allowed))
        invalid_statuses[field] = connection.execute(
            f"SELECT count(*) FROM gold_munic WHERE {field} NOT IN ({values})"
        ).fetchone()[0]
    _check(
        checks,
        "status_values_follow_contract",
        {field: count for field, count in invalid_statuses.items() if count},
        {},
    )

    conditional_conflicts = connection.execute(
        """
        SELECT count(*) FROM silver_munic
        WHERE municipal_civil_defense_body_status = 'declared_yes'
          AND civil_defense_budget_provision_status = 'not_applicable'
        """
    ).fetchone()[0]
    _check(
        checks,
        "budget_not_applicable_is_not_used_for_declared_compdec",
        conditional_conflicts,
        0,
    )

    yes_counts = {
        field: connection.execute(
            f"SELECT count(*) FROM silver_munic WHERE {field} = 'declared_yes'"
        ).fetchone()[0]
        for field in (
            "municipal_civil_defense_body_status",
            "flood_risk_mapping_status",
            "flood_contingency_plan_status",
            "flood_early_warning_status",
            "landslide_contingency_plan_status",
            "landslide_early_warning_status",
            "civil_defense_budget_provision_status",
            "civil_defense_early_warning_status",
        )
    }
    expected_yes_counts = {
        "municipal_civil_defense_body_status": 4236,
        "flood_risk_mapping_status": 2164,
        "flood_contingency_plan_status": 1407,
        "flood_early_warning_status": 436,
        "landslide_contingency_plan_status": 1016,
        "landslide_early_warning_status": 246,
        "civil_defense_budget_provision_status": 968,
        "civil_defense_early_warning_status": 435,
    }
    _check(checks, "selected_indicator_counts_match_2020_release", yes_counts, expected_yes_counts)

    failed = [check["name"] for check in checks if check["status"] == "FAIL"]
    return {
        "status": "PASS" if not failed else "FAIL",
        "generated_at": generated_at,
        "source": source_metadata,
        "rows": {"silver": source_rows, "gold": gold_rows},
        "coverage": {
            "source_municipalities": source_rows,
            "current_dimension_municipalities": gold_rows,
            "not_in_2020_source": not_in_source,
        },
        "declared_yes_counts": yes_counts,
        "checks": checks,
        "problems_found": failed,
        "warnings": [
            "As respostas foram declaradas pelas prefeituras e se referem a 2020.",
            "Recusa, nao informou, nao sabe e nao se aplica permanecem estados distintos.",
            "A variavel Mgrd201 usa o significado do questionario oficial: mapeamento de risco em encostas; o dicionario repete por engano o rotulo de inundacoes.",
            "Previsao orcamentaria e recursos da COMPDEC sao quesitos condicionais; nao se aplica nunca equivale a nao.",
        ],
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)


def write_munic_quality_reports(report: dict, *, json_path: Path, markdown_path: Path) -> None:
    _atomic_write(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    checks = "\n".join(
        f"| `{check['name']}` | {check['status']} | `{json.dumps(check['observed'], ensure_ascii=False)}` | `{json.dumps(check['expected'], ensure_ascii=False)}` |"
        for check in report["checks"]
    )
    counts = "\n".join(
        f"| `{field}` | {count} |" for field, count in report["declared_yes_counts"].items()
    )
    warnings = "\n".join(f"- {warning}" for warning in report["warnings"])
    markdown = f"""# MUNIC 2020 Data Quality Report

- Status: **{report['status']}**
- Gerado em: `{report['generated_at']}`
- SILVER: **{report['rows']['silver']}** linhas
- GOLD: **{report['rows']['gold']}** linhas
- Fora da fonte de 2020: `{report['coverage']['not_in_2020_source']}`

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
{checks}

## Contagens declaradas como Sim

| Indicador | Municipios |
|---|---:|
{counts}

## Ressalvas

{warnings}
"""
    _atomic_write(markdown_path, markdown)
