from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from src.config import (
    ATLAS_CORRECTION_FACTOR_PATH,
    ATLAS_DISCOVERY_URL,
    ATLAS_DISASTER_TYPE_PATH,
    ATLAS_DOC_PATH,
    ATLAS_FACT_PATH,
    ATLAS_MONTH_PROFILE_PATH,
    ATLAS_QUALITY_JSON_PATH,
    ATLAS_QUALITY_MARKDOWN_PATH,
    ATLAS_RAW_ROOT,
    ATLAS_RUNS_DIR,
    ATLAS_SILVER_PATH,
    ATLAS_SNAPSHOT_PATH,
    ATLAS_TYPE_SUMMARY_PATH,
    GOLD_PARQUET_PATH,
    PROJECT_ROOT,
)
from src.contracts.atlas import (
    known_variants,
    optional_fields,
    required_fields,
    unexpected_fields,
)
from src.extract.atlas import discover_and_acquire
from src.transform.atlas import create_atlas_tables, write_atlas_artifacts
from src.validation.atlas import validate_atlas, write_atlas_quality_reports


OUTPUT_PATHS = (
    ATLAS_SILVER_PATH,
    ATLAS_CORRECTION_FACTOR_PATH,
    ATLAS_DISASTER_TYPE_PATH,
    ATLAS_FACT_PATH,
    ATLAS_SNAPSHOT_PATH,
    ATLAS_TYPE_SUMMARY_PATH,
    ATLAS_MONTH_PROFILE_PATH,
    ATLAS_QUALITY_JSON_PATH,
    ATLAS_QUALITY_MARKDOWN_PATH,
    ATLAS_DOC_PATH,
)

TABLES = (
    "silver_disaster_event",
    "atlas_monetary_correction_factor",
    "dim_disaster_type",
    "fact_disaster_event",
    "snapshot_municipality_disaster_history",
    "municipality_disaster_type_summary",
    "municipality_disaster_month_profile",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _pipeline_fingerprint() -> str:
    files = (
        Path(__file__),
        PROJECT_ROOT / "src" / "config.py",
        PROJECT_ROOT / "src" / "contracts" / "atlas.py",
        PROJECT_ROOT / "src" / "extract" / "atlas.py",
        PROJECT_ROOT / "src" / "transform" / "atlas.py",
        PROJECT_ROOT / "src" / "validation" / "atlas.py",
        PROJECT_ROOT / "requirements.txt",
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(PROJECT_ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _schema_fingerprint(connection: duckdb.DuckDBPyConnection) -> str:
    schemas = {
        table: [
            (row[0], row[1])
            for row in connection.execute(f"DESCRIBE {table}").fetchall()
        ]
        for table in TABLES
    }
    payload = json.dumps(schemas, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _contract_fingerprint() -> str:
    payload = json.dumps(
        {
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "known_variants": known_variants,
            "unexpected_fields": unexpected_fields,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _output_key(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _output_hashes(paths: tuple[Path, ...] = OUTPUT_PATHS) -> dict[str, str]:
    return {
        _output_key(path): _file_sha256(path)
        for path in paths
        if path.exists()
    }


def _input_signature(source, resources) -> dict[str, Any]:
    return {
        "source_release": source.source_release,
        "source_official_date": source.source_official_date,
        "discovered_urls": source.discovered_urls,
        "source_hashes": {
            name: resource.manifest["sha256"]
            for name, resource in resources.items()
        },
        "dim_municipality_sha256": _file_sha256(GOLD_PARQUET_PATH),
    }


def is_unchanged(
    previous: dict[str, Any] | None,
    *,
    signature: dict[str, Any],
    pipeline_fingerprint: str,
    output_paths: tuple[Path, ...] = OUTPUT_PATHS,
) -> bool:
    current_hashes = _output_hashes(output_paths)
    previous_hashes = previous.get("output_hashes", {}) if previous else {}
    return bool(
        previous
        and previous.get("input_signature") == signature
        and previous.get("pipeline_fingerprint") == pipeline_fingerprint
        and len(current_hashes) == len(output_paths)
        and all(
            previous_hashes.get(path) == sha256
            for path, sha256 in current_hashes.items()
        )
    )


def _write_run_manifest(manifest: dict[str, Any], *, successful: bool) -> None:
    ATLAS_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_json(ATLAS_RUNS_DIR / f"{manifest['run_id']}.json", manifest)
    if successful:
        _atomic_json(ATLAS_RUNS_DIR / "latest_successful_run.json", manifest)


def _archive_previous_release(previous: dict[str, Any]) -> dict[str, Path]:
    release = previous["source_release"]
    destination = PROJECT_ROOT / "data" / "gold" / "atlas" / "history" / release
    destination.mkdir(parents=True, exist_ok=True)
    archived = {}
    for path in (
        ATLAS_DISASTER_TYPE_PATH,
        ATLAS_FACT_PATH,
        ATLAS_SNAPSHOT_PATH,
        ATLAS_TYPE_SUMMARY_PATH,
        ATLAS_MONTH_PROFILE_PATH,
    ):
        if path.exists():
            target = destination / path.name
            if not target.exists():
                shutil.copy2(path, target)
            archived[path.name] = target
    return archived


def _release_impact(
    connection: duckdb.DuckDBPyConnection,
    *,
    previous: dict[str, Any] | None,
    current_release: str,
    archived: dict[str, Path],
) -> dict[str, Any]:
    impact: dict[str, Any] = {
        "previous_release": previous.get("source_release") if previous else None,
        "current_release": current_release,
        "event_ids_added": None,
        "event_ids_removed": None,
        "municipality_codes_added": None,
        "municipality_codes_removed": None,
        "cobrade_codes_added": None,
        "cobrade_codes_removed": None,
        "schema_changes": None,
    }
    previous_fact = archived.get(ATLAS_FACT_PATH.name)
    previous_types = archived.get(ATLAS_DISASTER_TYPE_PATH.name)
    if not previous or not previous_fact or not previous_types:
        return impact
    fact_path = str(previous_fact).replace("'", "''")
    type_path = str(previous_types).replace("'", "''")
    event_changes = connection.execute(
        f"""
        SELECT
            (SELECT count(*) FROM fact_disaster_event c
             ANTI JOIN read_parquet('{fact_path}') p USING (disaster_event_id)),
            (SELECT count(*) FROM read_parquet('{fact_path}') p
             ANTI JOIN fact_disaster_event c USING (disaster_event_id)),
            (SELECT count(*) FROM (SELECT DISTINCT codigo_ibge FROM fact_disaster_event) c
             ANTI JOIN (SELECT DISTINCT codigo_ibge FROM read_parquet('{fact_path}')) p
                 USING (codigo_ibge)),
            (SELECT count(*) FROM (SELECT DISTINCT codigo_ibge FROM read_parquet('{fact_path}')) p
             ANTI JOIN (SELECT DISTINCT codigo_ibge FROM fact_disaster_event) c
                 USING (codigo_ibge)),
            (SELECT count(*) FROM dim_disaster_type c
             ANTI JOIN read_parquet('{type_path}') p USING (cobrade_code)),
            (SELECT count(*) FROM read_parquet('{type_path}') p
             ANTI JOIN dim_disaster_type c USING (cobrade_code))
        """
    ).fetchone()
    (
        impact["event_ids_added"],
        impact["event_ids_removed"],
        impact["municipality_codes_added"],
        impact["municipality_codes_removed"],
        impact["cobrade_codes_added"],
        impact["cobrade_codes_removed"],
    ) = event_changes
    old_schema = {
        row[0]: row[1]
        for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{fact_path}')"
        ).fetchall()
    }
    new_schema = {
        row[0]: row[1]
        for row in connection.execute("DESCRIBE fact_disaster_event").fetchall()
    }
    impact["schema_changes"] = {
        "columns_added": sorted(set(new_schema) - set(old_schema)),
        "columns_removed": sorted(set(old_schema) - set(new_schema)),
        "types_changed": {
            name: {"previous": old_schema[name], "current": new_schema[name]}
            for name in sorted(set(old_schema) & set(new_schema))
            if old_schema[name] != new_schema[name]
        },
    }
    return impact


def _schema_markdown(
    connection: duckdb.DuckDBPyConnection, table: str
) -> str:
    return "\n".join(
        f"| `{row[0]}` | `{row[1]}` |"
        for row in connection.execute(f"DESCRIBE {table}").fetchall()
    )


def _write_documentation(
    *, source, report: dict[str, Any], connection: duckdb.DuckDBPyConnection
) -> None:
    inspection = report["source_inspection"]
    matching = report["matching"]
    anomalies = report["anomalies_preserved"]
    source_columns = "\n".join(
        f"| `{name}` | `{data_type}` |"
        for name, data_type in inspection["workbook_source_columns"]
    )
    schemas = {
        table: _schema_markdown(connection, table)
        for table in (
            "dim_disaster_type",
            "fact_disaster_event",
            "snapshot_municipality_disaster_history",
            "municipality_disaster_type_summary",
            "municipality_disaster_month_profile",
        )
    }
    documentation = f"""# Atlas Digital de Desastres / S2ID

## Fonte e Release

- Fonte oficial: Atlas Digital de Desastres no Brasil / S2ID.
- Descoberta canonica: `{ATLAS_DISCOVERY_URL}`.
- Release: `{source.source_release}`.
- Data oficial identificada no nome do arquivo: `{source.source_official_date}`.
- Serie declarada: `{source.first_year}`–`{source.latest_year}`.
- Modo de descoberta: `{source.discovery_mode}`.
- CSV: `{source.discovered_urls['csv']}`.
- XLSX: `{source.discovered_urls['xlsx']}`.
- Manual: `{source.discovered_urls['manual']}`.
- Log de correcoes: `{source.discovered_urls['correction_log']}`.

O pipeline redescobre os quatro recursos na pagina oficial. URLs finais nao sao
fixadas no codigo. Overrides `ATLAS_CSV_URL`, `ATLAS_XLSX_URL`,
`ATLAS_MANUAL_URL` e `ATLAS_LOG_URL` existem apenas para recuperacao operacional
e ficam registrados no RAW.

## Execucao

```bash
python -m src.atlas
```

Uma assinatura combina release, URLs oficiais, hashes dos quatro recursos e o
fingerprint do pipeline. Se nada mudou e todos os artefatos existem, a execucao
termina em `NO_CHANGE` sem reconstruir os Parquets. Uma nova release preserva o
RAW anterior, arquiva as GOLDs e gera um relatorio de impacto.

## Inspecao da Fonte

- CSV `{inspection['encoding']}`, delimitador `{inspection['delimiter']}`, aspas
  `{inspection['quote_character']}` e fim de linha `{inspection['line_ending']}`.
- **{inspection['rows']}** registros logicos e **{inspection['physical_lines']}**
  linhas fisicas; narrativas entre aspas podem conter quebras de linha.
- **{inspection['column_count']}** colunas validadas em ordem exata.
- Eventos: `{inspection['first_event_date']}` a `{inspection['latest_event_date']}`.
- Registros: `{inspection['first_registration_date']}` a
  `{inspection['latest_registration_date']}`.
- **{inspection['municipality_count']}** codigos municipais observados.
- **{inspection['cobrade_count_observed']}** COBRADE observados e
  **{inspection['cobrade_count_dimension']}** na dimensao oficial do workbook.
- Valores monetarios corrigidos por IGP-DI para dezembro de
  **{inspection['correction_reference_year']}**, indice
  **{inspection['correction_reference_index']}**.

| Coluna original | Tipo observado no XLSX |
|---|---|
{source_columns}

O CSV de valores corrigidos e a entrada canonica dos eventos. O XLSX fornece a
dimensao COBRADE, os fatores de correcao e uma reconciliacao independente. O
pipeline exige igualdade dos IDs e dos 70 valores entre o CSV e a folha `Atlas
Valores Corrigidos`. O manual e o log sao preservados integralmente e seus hashes
participam da identidade da carga.

## Granularidades

- `silver_disaster_event`: uma linha por registro oficial, inclusive divergencias.
- `dim_disaster_type` (SILVER): uma linha por COBRADE presente na folha oficial.
- `fact_disaster_event`: `codigo_ibge + disaster_event_id`.
- `snapshot_municipality_disaster_history`: `codigo_ibge + reference_date`.
- `municipality_disaster_type_summary`: `codigo_ibge + cobrade_code`.
- `municipality_disaster_month_profile`: `codigo_ibge + month`.

O snapshot e o perfil mensal incluem toda a `dim_municipality`. Um zero significa
somente **0 eventos encontrados na fonte**, nunca ausencia comprovada de desastre.
As janelas de 5, 10 e 20 anos sao intervalos retroativos estritos a partir da
ultima data de evento da release.

A FACT preserva todos os registros, inclusive eventuais codigos historicos sem
correspondencia na dimensao vigente. Snapshots e perfis municipais agregam apenas
os registros associados por `codigo_ibge`, sem fallback por nome.

## Classificacao Derivada

- `is_hydrological`: grupo COBRADE oficial de codigo `12`.
- `is_geological`: grupo COBRADE oficial de codigo `11`.
- `is_rain_related`: inundacao `12100`, enxurrada `12200`, alagamento `12300`,
  chuvas intensas `13214` e movimentos de massa `11311`–`11340` enumerados na
  versao `atlas_cobrade_rain_v1`.

As flags sao classificacoes documentais versionadas, nao inferencias causais para
um evento particular. A FACT preserva todos os tipos de desastre.

## Matching e Qualidade

- Fonte: **{matching['source_municipalities']}** municipios.
- Matched por `codigo_ibge`: **{matching['matched_municipalities']}**.
- Fonte sem dimensao: **{matching['unmatched_source_municipalities']}**.
- Cobertura da dimensao: **{matching['municipality_coverage_pct']:.6f}%**.
- Dimensao sem registro: **{matching['dim_without_record_count']}**.
- Protocolos fora do formato: **{anomalies['invalid_protocol_format']}**.
- Conflitos protocolo/IBGE: **{anomalies['protocol_ibge_conflicts']}**.
- Conflitos protocolo/COBRADE: **{anomalies['protocol_cobrade_conflicts']}**.
- Evento posterior ao registro: **{anomalies['event_after_registration']}**.
- Grupos duplicados na chave natural: **{anomalies['natural_key_duplicate_groups']}**.

`Cod_IBGE_Mun`, `Cod_Cobrade`, `Data_Evento` e `Data_Registro` sao campos
canonicos da linha. O protocolo e um identificador opaco: suas partes nao
sobrescrevem os campos explicitos. Registros com a mesma chave natural e IDs
distintos nao sao deduplicados.

`direct_human_damage_total` reproduz a soma oficial de mortos, feridos, enfermos,
desabrigados, desalojados, desaparecidos e afetados por seca/estiagem.
`reported_affected_total` adiciona `other_affected`. Totais monetarios admitem
R$ 0,05 de diferenca por arredondamento dos componentes exibidos.

## Schema `dim_disaster_type`

| Nome | Tipo |
|---|---|
{schemas['dim_disaster_type']}

## Schema `fact_disaster_event`

| Nome | Tipo |
|---|---|
{schemas['fact_disaster_event']}

## Schema `snapshot_municipality_disaster_history`

| Nome | Tipo |
|---|---|
{schemas['snapshot_municipality_disaster_history']}

## Schema `municipality_disaster_type_summary`

| Nome | Tipo |
|---|---|
{schemas['municipality_disaster_type_summary']}

## Schema `municipality_disaster_month_profile`

| Nome | Tipo |
|---|---|
{schemas['municipality_disaster_month_profile']}

## Cautelas

- Os registros refletem o conhecimento informado no FIDE no momento do registro.
- A digitacao historica e a operacao do S2ID possuem metodologias diferentes.
- Reconhecimento federal e derivado somente de `Status = 'Reconhecido'`.
- Sazonalidade historica nao e probabilidade.
- Nenhuma tabela calcula risco, ranking, causalidade ou previsao.

O relatorio detalhado esta em `docs/atlas-data-quality-report.md`.
"""
    ATLAS_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = ATLAS_DOC_PATH.with_suffix(".md.tmp")
    temporary.write_text(documentation, encoding="utf-8")
    temporary.replace(ATLAS_DOC_PATH)


def run() -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    try:
        source, resources, discovery = discover_and_acquire(
            discovery_url=ATLAS_DISCOVERY_URL,
            raw_root=ATLAS_RAW_ROOT,
            checked_at=started_at,
        )
    except Exception as error:
        manifest = {
            "run_id": run_id,
            "source": "atlas",
            "source_release": None,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "discovery_urls": [ATLAS_DISCOVERY_URL],
            "resolved_urls": {},
            "source_hashes": {},
            "rows_raw": 0,
            "rows_silver": 0,
            "rows_gold": 0,
            "municipality_coverage_pct": None,
            "schema_fingerprint": None,
            "pipeline_fingerprint": _pipeline_fingerprint(),
            "status": "BLOCKED_SOURCE",
            "error": str(error),
        }
        _write_run_manifest(manifest, successful=False)
        raise

    fingerprint = _pipeline_fingerprint()
    signature = _input_signature(source, resources)
    latest_path = ATLAS_RUNS_DIR / "latest_successful_run.json"
    previous = _load_json(latest_path)
    if is_unchanged(
        previous, signature=signature, pipeline_fingerprint=fingerprint
    ):
        previous_report = _load_json(ATLAS_QUALITY_JSON_PATH)
        if not previous_report or previous_report.get("status") != "PASS":
            raise RuntimeError("Artefatos Atlas existentes nao possuem relatorio PASS")
        finished_at = datetime.now(timezone.utc).replace(microsecond=0)
        manifest = {
            **{key: value for key, value in previous.items() if key != "status"},
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "discovery_urls": [source.discovery_url],
            "resolved_urls": {
                name: resource.manifest["resolved_download_url"]
                for name, resource in resources.items()
            },
            "source_hashes": {
                name: resource.manifest["sha256"]
                for name, resource in resources.items()
            },
            "input_signature": signature,
            "discovery_manifest": discovery,
            "output_hashes": _output_hashes(),
            "status": "NO_CHANGE",
        }
        _write_run_manifest(manifest, successful=True)
        return manifest

    resource_manifests = {
        name: resource.manifest for name, resource in resources.items()
    }
    try:
        with tempfile.TemporaryDirectory(prefix="antes_da_chuva_atlas_") as temp_dir:
            connection = duckdb.connect(str(Path(temp_dir) / "atlas.duckdb"))
            try:
                inspection = create_atlas_tables(
                    connection,
                    csv_path=resources["csv"].artifact_path,
                    xlsx_path=resources["xlsx"].artifact_path,
                    correction_log_path=resources["correction_log"].artifact_path,
                    manual_path=resources["manual"].artifact_path,
                    dim_municipality_path=GOLD_PARQUET_PATH,
                    source_release=source.source_release,
                    source_url=source.discovered_urls["csv"],
                    source_official_date=source.source_official_date,
                    csv_sha256=resources["csv"].manifest["sha256"],
                    xlsx_sha256=resources["xlsx"].manifest["sha256"],
                    correction_log_sha256=resources["correction_log"].manifest["sha256"],
                    manual_sha256=resources["manual"].manifest["sha256"],
                    ingested_at=started_at,
                )
                report = validate_atlas(
                    connection,
                    inspection=inspection,
                    source_release=source.source_release,
                    source_official_date=source.source_official_date,
                    source_first_year=source.first_year,
                    source_latest_year=source.latest_year,
                    resources=resource_manifests,
                    dim_municipality_path=GOLD_PARQUET_PATH,
                    generated_at=started_at,
                )
                if report["status"] != "PASS":
                    raise RuntimeError(
                        "A carga Atlas falhou: " + ", ".join(report["problems_found"])
                    )
                write_atlas_quality_reports(
                    report,
                    json_path=ATLAS_QUALITY_JSON_PATH,
                    markdown_path=ATLAS_QUALITY_MARKDOWN_PATH,
                )
                is_new_release = bool(
                    previous
                    and previous.get("source_release") != source.source_release
                )
                archived = _archive_previous_release(previous) if is_new_release else {}
                impact = _release_impact(
                    connection,
                    previous=previous if is_new_release else None,
                    current_release=source.source_release,
                    archived=archived,
                )
                write_atlas_artifacts(
                    connection,
                    silver_path=ATLAS_SILVER_PATH,
                    correction_factor_path=ATLAS_CORRECTION_FACTOR_PATH,
                    disaster_type_path=ATLAS_DISASTER_TYPE_PATH,
                    fact_path=ATLAS_FACT_PATH,
                    snapshot_path=ATLAS_SNAPSHOT_PATH,
                    type_summary_path=ATLAS_TYPE_SUMMARY_PATH,
                    month_profile_path=ATLAS_MONTH_PROFILE_PATH,
                )
                _write_documentation(
                    source=source, report=report, connection=connection
                )
                schema_fingerprint = _schema_fingerprint(connection)
            finally:
                connection.close()

        impact_name = (
            f"{impact['previous_release']}_to_{source.source_release}_impact.json"
            if impact["previous_release"]
            else f"{source.source_release}_initial_impact.json"
        )
        impact_path = ATLAS_RUNS_DIR / impact_name
        _atomic_json(impact_path, impact)
        finished_at = datetime.now(timezone.utc).replace(microsecond=0)
        rows_gold = sum(
            report["rows"][key]
            for key in (
                "fact",
                "snapshot",
                "type_summary",
                "month_profile",
            )
        )
        manifest = {
            "run_id": run_id,
            "source": "atlas",
            "source_release": source.source_release,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "discovery_urls": [source.discovery_url],
            "resolved_urls": report["resolved_urls"],
            "source_hashes": report["source_hashes"],
            "rows_raw": report["rows"]["raw"],
            "rows_silver": report["rows"]["silver"],
            "rows_gold": rows_gold,
            "rows": report["rows"],
            "municipality_coverage_pct": report["matching"][
                "municipality_coverage_pct"
            ],
            "schema_fingerprint": schema_fingerprint,
            "source_contract_fingerprint": _contract_fingerprint(),
            "pipeline_fingerprint": fingerprint,
            "input_signature": signature,
            "output_hashes": _output_hashes(),
            "discovery_manifest": discovery,
            "release_impact_report": str(impact_path),
            "status": "PASS",
        }
        _write_run_manifest(manifest, successful=True)
        return manifest
    except Exception as error:
        failure = {
            "run_id": run_id,
            "source": "atlas",
            "source_release": source.source_release,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "discovery_urls": [source.discovery_url],
            "resolved_urls": {
                name: resource.manifest["resolved_download_url"]
                for name, resource in resources.items()
            },
            "source_hashes": {
                name: resource.manifest["sha256"]
                for name, resource in resources.items()
            },
            "rows_raw": 0,
            "rows_silver": 0,
            "rows_gold": 0,
            "municipality_coverage_pct": None,
            "schema_fingerprint": None,
            "pipeline_fingerprint": fingerprint,
            "status": "FAILED",
            "error": str(error),
        }
        _write_run_manifest(failure, successful=False)
        raise


if __name__ == "__main__":
    result = run()
    print(
        f"Atlas {result['source_release']} {result['status']}: "
        f"{result['rows']['fact']} eventos FACT, cobertura municipal "
        f"{result['municipality_coverage_pct']:.6f}%."
    )
