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
    GOLD_PARQUET_PATH,
    MAPBIOMAS_CHANGE_PATH,
    MAPBIOMAS_CLASS_LEGEND_PATH,
    MAPBIOMAS_COVERAGE_URL,
    MAPBIOMAS_DOC_PATH,
    MAPBIOMAS_FACT_PATH,
    MAPBIOMAS_LEGEND_DISCOVERY_URL,
    MAPBIOMAS_QUALITY_JSON_PATH,
    MAPBIOMAS_QUALITY_MARKDOWN_PATH,
    MAPBIOMAS_RAW_ROOT,
    MAPBIOMAS_RUNS_DIR,
    MAPBIOMAS_SILVER_PATH,
    MAPBIOMAS_SNAPSHOT_PATH,
    MAPBIOMAS_STATISTICS_DISCOVERY_URL,
    MAPBIOMAS_URBANIZATION_URL,
    PROJECT_ROOT,
)
from src.extract.mapbiomas import discover_and_acquire
from src.transform.mapbiomas import (
    create_mapbiomas_tables,
    write_mapbiomas_artifacts,
)
from src.validation.mapbiomas import (
    validate_mapbiomas,
    write_mapbiomas_quality_reports,
)


OUTPUT_PATHS = (
    MAPBIOMAS_SILVER_PATH,
    MAPBIOMAS_CLASS_LEGEND_PATH,
    MAPBIOMAS_FACT_PATH,
    MAPBIOMAS_SNAPSHOT_PATH,
    MAPBIOMAS_CHANGE_PATH,
    MAPBIOMAS_QUALITY_JSON_PATH,
    MAPBIOMAS_QUALITY_MARKDOWN_PATH,
    MAPBIOMAS_DOC_PATH,
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _pipeline_fingerprint() -> str:
    files = (
        Path(__file__),
        PROJECT_ROOT / "src" / "config.py",
        PROJECT_ROOT / "src" / "extract" / "mapbiomas.py",
        PROJECT_ROOT / "src" / "transform" / "mapbiomas.py",
        PROJECT_ROOT / "src" / "validation" / "mapbiomas.py",
        PROJECT_ROOT / "requirements.txt",
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(PROJECT_ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _input_signature(source, statistics, legend) -> dict[str, Any]:
    return {
        "collection_id": source.collection_id,
        "collection_version": source.collection_version,
        "statistics_url": source.statistics_url,
        "statistics_sha256": statistics.manifest["sha256"],
        "legend_url": source.legend_url,
        "legend_sha256": legend.manifest["sha256"],
    }


def _output_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(PROJECT_ROOT)): _file_sha256(path)
        for path in OUTPUT_PATHS
        if path.exists()
    }


def _write_run_manifest(manifest: dict[str, Any]) -> None:
    MAPBIOMAS_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_json(MAPBIOMAS_RUNS_DIR / f"{manifest['run_id']}.json", manifest)
    _atomic_json(MAPBIOMAS_RUNS_DIR / "latest_successful_run.json", manifest)


def _archive_previous_gold(previous: dict[str, Any]) -> dict[str, Path]:
    collection_id = previous["collection_id"]
    destination = (
        PROJECT_ROOT / "data" / "gold" / "mapbiomas" / "history"
        / f"collection_{collection_id}"
    )
    destination.mkdir(parents=True, exist_ok=True)
    archived = {}
    for path in (
        MAPBIOMAS_FACT_PATH,
        MAPBIOMAS_SNAPSHOT_PATH,
        MAPBIOMAS_CHANGE_PATH,
        MAPBIOMAS_CLASS_LEGEND_PATH,
    ):
        if path.exists():
            target = destination / path.name
            if not target.exists():
                shutil.copy2(path, target)
            archived[path.name] = target
    return archived


def _schema(connection: duckdb.DuckDBPyConnection, table: str) -> list[tuple[str, str]]:
    return [(row[0], row[1]) for row in connection.execute(f"DESCRIBE {table}").fetchall()]


def _write_collection_impact(
    *,
    previous: dict[str, Any] | None,
    current_report: dict[str, Any],
    connection: duckdb.DuckDBPyConnection,
    archived: dict[str, Path],
) -> dict[str, Any]:
    current = {
        "previous_collection": previous.get("collection_id") if previous else None,
        "current_collection": current_report["collection_id"],
        "previous_latest_year": previous.get("latest_year") if previous else None,
        "current_latest_year": current_report["source_inspection"]["latest_year"],
        "rows_previous": previous.get("rows") if previous else None,
        "rows_current": current_report["rows"],
        "class_ids_added": [],
        "class_ids_removed": [],
        "municipalities_added": [],
        "municipalities_removed": [],
        "schema_changes": {},
        "common_year_indicator_comparison": None,
    }
    if not previous:
        return current

    previous_legend = archived.get(MAPBIOMAS_CLASS_LEGEND_PATH.name)
    previous_snapshot = archived.get(MAPBIOMAS_SNAPSHOT_PATH.name)
    if not previous_legend or not previous_snapshot:
        current["schema_changes"] = {
            "status": "previous_gold_not_available_for_comparison"
        }
        return current

    previous_classes = {
        row[0]
        for row in connection.execute(
            f"SELECT class_id FROM read_parquet('{str(previous_legend).replace("'", "''")}') "
            "WHERE is_in_statistics"
        ).fetchall()
    }
    current_classes = {
        row[0]
        for row in connection.execute(
            "SELECT class_id FROM mapbiomas_class_legend WHERE is_in_statistics"
        ).fetchall()
    }
    current["class_ids_added"] = sorted(current_classes - previous_classes)
    current["class_ids_removed"] = sorted(previous_classes - current_classes)

    previous_municipalities = {
        row[0]
        for row in connection.execute(
            f"SELECT DISTINCT codigo_ibge FROM read_parquet('{str(previous_snapshot).replace("'", "''")}')"
        ).fetchall()
    }
    current_municipalities = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT codigo_ibge FROM snapshot_municipality_land_cover"
        ).fetchall()
    }
    current["municipalities_added"] = sorted(
        current_municipalities - previous_municipalities
    )
    current["municipalities_removed"] = sorted(
        previous_municipalities - current_municipalities
    )

    previous_schema = connection.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{str(previous_snapshot).replace("'", "''")}')"
    ).fetchall()
    current_schema = connection.execute(
        "DESCRIBE snapshot_municipality_land_cover"
    ).fetchall()
    previous_schema_map = {row[0]: row[1] for row in previous_schema}
    current_schema_map = {row[0]: row[1] for row in current_schema}
    current["schema_changes"] = {
        "columns_added": sorted(set(current_schema_map) - set(previous_schema_map)),
        "columns_removed": sorted(set(previous_schema_map) - set(current_schema_map)),
        "types_changed": {
            column: {
                "previous": previous_schema_map[column],
                "current": current_schema_map[column],
            }
            for column in sorted(set(previous_schema_map) & set(current_schema_map))
            if previous_schema_map[column] != current_schema_map[column]
        },
    }

    common_year = min(
        int(previous["latest_year"]),
        int(current_report["source_inspection"]["latest_year"]),
    )
    comparison = connection.execute(
        f"""
        WITH previous AS (
            SELECT * FROM read_parquet('{str(previous_snapshot).replace("'", "''")}')
            WHERE year = {common_year}
        ), current AS (
            SELECT * FROM snapshot_municipality_land_cover
            WHERE year = {common_year}
        )
        SELECT
            count(*),
            avg(abs(c.urban_area_ha - p.urban_area_ha)),
            max(abs(c.urban_area_ha - p.urban_area_ha)),
            avg(abs(c.native_vegetation_area_ha - p.native_vegetation_area_ha)),
            max(abs(c.native_vegetation_area_ha - p.native_vegetation_area_ha))
        FROM current c
        JOIN previous p USING (codigo_ibge)
        """
    ).fetchone()
    current["common_year_indicator_comparison"] = {
        "year": common_year,
        "municipalities_compared": comparison[0],
        "urban_area_mean_absolute_difference_ha": comparison[1],
        "urban_area_max_absolute_difference_ha": comparison[2],
        "native_vegetation_mean_absolute_difference_ha": comparison[3],
        "native_vegetation_max_absolute_difference_ha": comparison[4],
    }
    return current


COLUMN_DESCRIPTIONS = {
    "codigo_ibge": "Codigo territorial usado no relacionamento com dim_municipality.",
    "year": "Ano da classificacao MapBiomas.",
    "class_id": "Codigo oficial da classe de cobertura e uso da terra.",
    "class_name": "Nome oficial da classe; fallback auditavel do workbook quando ausente no CSV.",
    "class_level": "Nivel terminal derivado da hierarquia oficial do workbook.",
    "area_ha": "Area classificada em hectares.",
    "area_km2": "Area em quilometros quadrados, calculada como hectares / 100.",
    "mapped_area_ha": "Soma das classes terminais, excluindo Not Observed.",
    "urban_area_ha": "Area classificada como Area Urbanizada, em hectares.",
    "urban_area_km2": "Area classificada como Area Urbanizada, em km2.",
    "urban_area_pct": "Area Urbanizada dividida pela area mapeada, em percentual.",
    "native_vegetation_area_ha": "Soma dos ramos naturais selecionados, em hectares.",
    "native_vegetation_area_km2": "Soma dos ramos naturais selecionados, em km2.",
    "native_vegetation_area_pct": "Vegetacao nativa dividida pela area mapeada.",
    "agriculture_livestock_area_ha": "Ramo terminal Agropecuaria/Farming, em hectares.",
    "agriculture_livestock_area_km2": "Ramo terminal Agropecuaria/Farming, em km2.",
    "agriculture_livestock_area_pct": "Agropecuaria dividida pela area mapeada.",
    "water_area_ha": "Area de Rio, Lago e Oceano, em hectares.",
    "water_area_km2": "Area de Rio, Lago e Oceano, em km2.",
    "water_area_pct": "Rio, Lago e Oceano dividido pela area mapeada.",
    "wetland_area_ha": "Campo Alagado e Area Pantanosa, em hectares.",
    "wetland_area_km2": "Campo Alagado e Area Pantanosa, em km2.",
    "wetland_area_pct": "Campo Alagado e Area Pantanosa dividido pela area mapeada.",
    "collection_id": "Identificador da colecao MapBiomas.",
    "collection_version": "Versao da tabela estatistica na pagina oficial.",
    "source_sha256": "SHA-256 do arquivo ZIP estatistico oficial.",
    "source_publication_date": "Data de publicacao declarada na pagina oficial.",
    "ingested_at": "Timestamp UTC da execucao que materializou os dados.",
}


def _schema_markdown(
    connection: duckdb.DuckDBPyConnection, table: str
) -> str:
    rows = []
    for name, data_type in _schema(connection, table):
        description = COLUMN_DESCRIPTIONS.get(
            name,
            name.replace("_", " ").capitalize() + ".",
        )
        rows.append(f"| `{name}` | `{data_type}` | {description} |")
    return "\n".join(rows)


def _write_documentation(
    *,
    source,
    report: dict[str, Any],
    connection: duckdb.DuckDBPyConnection,
) -> None:
    inspection = report["source_inspection"]
    semantics = report["class_semantics"]
    area_check = next(
        check
        for check in report["checks"]
        if check["name"] == "mapped_municipality_area_is_positive_and_stable"
    )
    statistics_columns = "\n".join(
        f"| `{name}` | `{data_type}` |"
        for name, data_type in inspection["source_columns"]
    )
    fact_schema = _schema_markdown(connection, "fact_municipality_land_cover")
    snapshot_schema = _schema_markdown(
        connection, "snapshot_municipality_land_cover"
    )
    change_schema = _schema_markdown(
        connection, "municipality_land_cover_change"
    )
    documentation = f"""# MapBiomas - Cobertura e Uso da Terra

## Fonte

- Fonte semantica: MapBiomas Brasil.
- Produto: Cobertura e Uso da Terra - Cobertura 30m.
- Pagina canonica: `{MAPBIOMAS_COVERAGE_URL}`.
- Pagina de estatisticas: `{MAPBIOMAS_STATISTICS_DISCOVERY_URL}`.
- Pagina de legenda: `{MAPBIOMAS_LEGEND_DISCOVERY_URL}`.
- Referencia de urbanizacao: `{MAPBIOMAS_URBANIZATION_URL}`.
- Resolucao original: 30 metros.
- Unidade estatistica ingerida: hectares.
- Colecao detectada: `{source.collection_name}`.
- Versao da tabela: `{source.collection_version}`.
- Serie detectada: `{source.first_year}–{source.latest_year}`.
- Publicacao detectada: `{source.source_publication_date}`.
- Modo de descoberta: `{source.discovery_mode}`.
- Asset GEE apenas para linhagem: `{source.earth_engine_asset}`.

O pipeline parte das paginas oficiais e exige concordancia entre a pagina do
produto e a pagina de estatisticas. Google Drive e somente infraestrutura de
distribuicao. `MAPBIOMAS_STATISTICS_URL` e `MAPBIOMAS_LEGEND_URL` sao overrides
de emergencia registrados como `discovery_mode=override`.

## Execucao

```bash
python -m src.mapbiomas
```

Na ausencia de mudanca de colecao, URLs, hashes e codigo do pipeline, uma nova
checagem e registrada mas os Parquets nao sao reconstruidos. Nova colecao
reconstroi toda a serie, nao apenas o ultimo ano, preserva os RAW anteriores e
gera relatorio de impacto.

## RAW e Schema Encontrado

O recurso oficial e um ZIP contendo XLSX. Folhas encontradas:
`{inspection['workbook_sheets']}`. A folha de dados possui
**{inspection['rows_wide']}** linhas, **{inspection['biomes']}** biomas,
**{inspection['states']}** estados, **{inspection['municipalities']}** geocodigos
e anos em colunas `yAAAA`.

| Coluna original | Tipo aparente DuckDB |
|---|---|
{statistics_columns}

A legenda e CSV `{inspection['legend_encoding']}`, delimitado por
`{inspection['legend_delimiter']}`, com colunas `{inspection['legend_columns']}`.
O XLSX possui as classes `{inspection['classes_statistics_only']}` ausentes do
CSV; o CSV possui `{inspection['classes_legend_only']}` ausentes das estatisticas.
Nesses casos a hierarquia oficial do workbook e preservada e sua origem fica
explicita em `mapbiomas_class_legend.parquet`.

## Granularidades

- RAW: uma linha larga por geocodigo, bioma e classe terminal, com anos em colunas.
- SILVER: colecao x geocodigo x bioma x ano x classe.
- FACT: municipio canonico x ano x classe, apos `SUM` de todos os biomas.
- SNAPSHOT: municipio canonico x ano.
- CHANGE: municipio canonico, com primeiro/ultimo ano e janelas dinamicas.

Existem **{inspection['municipalities_in_multiple_biomes']}** geocodigos em mais
de um bioma. Nenhum bioma e escolhido por `MAX` ou por prioridade. A unica
duplicidade no grao RAW e consolidada por soma na SILVER, que preserva
`source_row_count`, `source_state_names` e `source_region_names`.

## Hierarquia e Agregacoes

A tabela estatistica contem classes terminais. `class_level` e derivado do ultimo
nivel distinto em `class_level_1..4`; classes pai nao sao somadas aos filhos.

- Area urbanizada: classe `{semantics['urban_class_id']}`, resolvida no CSV e conferida na pagina de Urbanizacao Anual.
- Agua: classe `{semantics['water_class_id']}` (`Rio, Lago e Oceano`).
- Campo alagado/area pantanosa: classe `{semantics['wetland_class_id']}`.
- `native_vegetation_class_ids`: `{semantics['native_vegetation_class_ids']}`.
- `agriculture_livestock_class_ids`: `{semantics['agriculture_livestock_class_ids']}`.
- Classes excluidas do denominador como `Not Observed`: `{semantics['not_observed_class_ids']}`.

Vegetacao nativa e derivada dos ramos oficiais `Forest` e
`Herbaceous and Shrubby Vegetation`. Agropecuaria e derivada de todos os filhos
terminais de `Farming`. As listas sao recalculadas e versionadas por colecao.

`mapped_area_ha` soma classes terminais mutuamente exclusivas, exceto `Not
Observed`. A maior variacao observada entre anos foi
`{area_check['observed']['max_variation_pct']:.6f}%`; apos observar a
distribuicao, adotou-se 0,1% como alerta e 1% como falha.

Os percentuais selecionados nao somam necessariamente 100%. Em particular,
campo alagado e area pantanosa integra o ramo de vegetacao nativa e aparece
tambem como indicador proprio.

## Matching Municipal

- Geocodigos MapBiomas: `{report['matching']['municipios_mapbiomas']}`.
- Codigos da dimensao: `{report['matching']['municipios_dim_municipality']}`.
- Matched: `{report['matching']['municipios_matched']}`.
- Cobertura: `{report['matching']['coverage_pct']:.6f}%`.
- MapBiomas sem dimensao: `{report['matching']['codigo_mapbiomas_sem_dim']}`.
- Dimensao sem MapBiomas: `{report['matching']['codigo_dim_sem_mapbiomas']}`.

Os codigos extras atuais representam Lagoa Mirim e Lagoa dos Patos. Fernando de
Noronha nao aparece na tabela estatistica. Nenhum matching por nome e aplicado.

## Schema FACT

| Nome | Tipo | Descricao |
|---|---|---|
{fact_schema}

## Schema Snapshot

| Nome | Tipo | Descricao |
|---|---|---|
{snapshot_schema}

## Schema Changes

| Nome | Tipo | Descricao |
|---|---|---|
{change_schema}

## Cautelas Metodologicas

- MapBiomas e uma classificacao por sensoriamento remoto, nao um cadastro fisico do solo.
- Colecoes novas podem revisar toda a serie historica.
- Area urbanizada nao e sinônimo de superficie impermeabilizada.
- Campo alagado e area pantanosa nao e mapa de risco.
- Agua superficial nao equivale a disponibilidade hidrica.
- Correlacao temporal nao demonstra causalidade.
- Nenhum indicador desta camada mede risco, vulnerabilidade ou resiliencia.
- GeoTIFF e Google Earth Engine nao sao usados neste pipeline.

O relatorio completo esta em `docs/mapbiomas-data-quality-report.md` e o
manifest estruturado em `data/gold/mapbiomas_data_quality_report.json`.
"""
    MAPBIOMAS_DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = MAPBIOMAS_DOC_PATH.with_suffix(".md.tmp")
    temporary_path.write_text(documentation, encoding="utf-8")
    temporary_path.replace(MAPBIOMAS_DOC_PATH)


def run() -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    source, statistics, legend, discovery_pages = discover_and_acquire(
        coverage_url=MAPBIOMAS_COVERAGE_URL,
        statistics_discovery_url=MAPBIOMAS_STATISTICS_DISCOVERY_URL,
        legend_discovery_url=MAPBIOMAS_LEGEND_DISCOVERY_URL,
        urbanization_url=MAPBIOMAS_URBANIZATION_URL,
        raw_root=MAPBIOMAS_RAW_ROOT,
        downloaded_at=started_at,
    )
    if statistics.extracted_path is None:
        raise RuntimeError("O ZIP estatistico nao produziu uma planilha XLSX")
    if _file_sha256(statistics.artifact_path) != statistics.manifest["sha256"]:
        raise RuntimeError("SHA-256 do RAW estatistico diverge do manifesto")
    if _file_sha256(legend.artifact_path) != legend.manifest["sha256"]:
        raise RuntimeError("SHA-256 do RAW da legenda diverge do manifesto")

    fingerprint = _pipeline_fingerprint()
    signature = _input_signature(source, statistics, legend)
    latest_manifest_path = MAPBIOMAS_RUNS_DIR / "latest_successful_run.json"
    previous = _load_json(latest_manifest_path)
    unchanged = bool(
        previous
        and previous.get("input_signature") == signature
        and previous.get("pipeline_fingerprint") == fingerprint
        and all(path.exists() and path.stat().st_size > 0 for path in OUTPUT_PATHS)
    )
    if unchanged:
        previous_report = _load_json(MAPBIOMAS_QUALITY_JSON_PATH)
        if not previous_report or previous_report.get("status") != "PASS":
            raise RuntimeError("Artefatos existentes nao possuem relatorio PASS")
        finished_at = datetime.now(timezone.utc).replace(microsecond=0)
        run_manifest = {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "collection_id": source.collection_id,
            "collection_version": source.collection_version,
            "first_year": source.first_year,
            "latest_year": source.latest_year,
            "source_urls": previous_report["source_urls"],
            "source_hashes": previous_report["source_hashes"],
            "rows": previous_report["rows"],
            "rows_raw": previous_report["rows"]["raw_wide"],
            "rows_silver": previous_report["rows"]["silver"],
            "rows_fact": previous_report["rows"]["fact"],
            "rows_snapshot": previous_report["rows"]["snapshot"],
            "rows_change": previous_report["rows"]["change"],
            "municipality_coverage_pct": previous_report["matching"]["coverage_pct"],
            "input_signature": signature,
            "pipeline_fingerprint": fingerprint,
            "output_hashes": _output_hashes(),
            "discovery_pages": discovery_pages,
            "status": "NO_CHANGE",
        }
        _write_run_manifest(run_manifest)
        return run_manifest

    archived = {}
    is_new_collection = bool(
        previous and previous.get("collection_id") != source.collection_id
    )
    if is_new_collection:
        archived = _archive_previous_gold(previous)

    with tempfile.TemporaryDirectory(prefix="antes_da_chuva_mapbiomas_") as temp_dir:
        connection = duckdb.connect(str(Path(temp_dir) / "mapbiomas.duckdb"))
        try:
            inspection, semantics = create_mapbiomas_tables(
                connection,
                xlsx_path=statistics.extracted_path,
                legend_path=legend.artifact_path,
                dim_municipality_path=GOLD_PARQUET_PATH,
                collection_id=source.collection_id,
                collection_version=source.collection_version,
                expected_first_year=source.first_year,
                expected_latest_year=source.latest_year,
                source_filename=statistics.extracted_path.name,
                source_sha256=statistics.manifest["sha256"],
                source_member_sha256=statistics.manifest["extracted_sha256"],
                legend_sha256=legend.manifest["sha256"],
                source_url=source.statistics_url,
                source_publication_date=source.source_publication_date,
                ingested_at=started_at,
                urban_class_id_from_documentation=source.urban_class_id,
            )
            report = validate_mapbiomas(
                connection,
                inspection=inspection,
                semantics=semantics,
                collection_id=source.collection_id,
                collection_version=source.collection_version,
                statistics_manifest=statistics.manifest,
                legend_manifest=legend.manifest,
                dim_municipality_path=GOLD_PARQUET_PATH,
                generated_at=started_at,
            )
            write_mapbiomas_quality_reports(
                report,
                json_path=MAPBIOMAS_QUALITY_JSON_PATH,
                markdown_path=MAPBIOMAS_QUALITY_MARKDOWN_PATH,
            )
            if report["status"] != "PASS":
                raise RuntimeError(
                    "A carga MapBiomas falhou: "
                    + ", ".join(report["problems_found"])
                )
            write_mapbiomas_artifacts(
                connection,
                silver_path=MAPBIOMAS_SILVER_PATH,
                class_legend_path=MAPBIOMAS_CLASS_LEGEND_PATH,
                fact_path=MAPBIOMAS_FACT_PATH,
                snapshot_path=MAPBIOMAS_SNAPSHOT_PATH,
                change_path=MAPBIOMAS_CHANGE_PATH,
            )
            _write_documentation(source=source, report=report, connection=connection)
            impact = _write_collection_impact(
                previous=previous if is_new_collection else None,
                current_report=report,
                connection=connection,
                archived=archived,
            )
        finally:
            connection.close()

    impact_path = (
        MAPBIOMAS_RUNS_DIR
        / (
            f"collection_{impact['previous_collection']}_to_"
            f"{impact['current_collection']}_impact.json"
            if impact["previous_collection"]
            else f"collection_{impact['current_collection']}_initial_impact.json"
        )
    )
    _atomic_json(impact_path, impact)
    finished_at = datetime.now(timezone.utc).replace(microsecond=0)
    run_manifest = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "collection_id": source.collection_id,
        "collection_version": source.collection_version,
        "first_year": source.first_year,
        "latest_year": source.latest_year,
        "source_urls": report["source_urls"],
        "source_hashes": report["source_hashes"],
        "rows": report["rows"],
        "rows_raw": report["rows"]["raw_wide"],
        "rows_silver": report["rows"]["silver"],
        "rows_fact": report["rows"]["fact"],
        "rows_snapshot": report["rows"]["snapshot"],
        "rows_change": report["rows"]["change"],
        "municipality_coverage_pct": report["matching"]["coverage_pct"],
        "input_signature": signature,
        "pipeline_fingerprint": fingerprint,
        "output_hashes": _output_hashes(),
        "discovery_pages": discovery_pages,
        "collection_impact_report": str(impact_path),
        "status": "PASS",
    }
    _write_run_manifest(run_manifest)
    return run_manifest


if __name__ == "__main__":
    result = run()
    print(
        f"MapBiomas colecao {result['collection_id']} {result['status']}: "
        f"{result['rows_fact']} linhas FACT, "
        f"cobertura municipal {result['municipality_coverage_pct']:.6f}%."
    )
