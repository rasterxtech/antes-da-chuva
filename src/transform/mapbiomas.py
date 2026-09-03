from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import duckdb


EXPECTED_SOURCE_COLUMNS = (
    "ID",
    "country",
    "biome",
    "region",
    "state",
    "geocode",
    "municipality",
    "municipality-state",
    "class",
    "class_level_0",
    "class_level_1",
    "class_level_2",
    "class_level_3",
    "class_level_4",
)


@dataclass(frozen=True)
class ClassSemantics:
    urban_class_id: int
    water_class_id: int
    wetland_class_id: int
    not_observed_class_ids: tuple[int, ...]
    native_vegetation_class_ids: tuple[int, ...]
    agriculture_livestock_class_ids: tuple[int, ...]
    mapped_class_ids: tuple[int, ...]


@dataclass(frozen=True)
class SourceInspection:
    format: str
    workbook_sheets: tuple[str, ...]
    source_columns: tuple[tuple[str, str], ...]
    year_columns: tuple[str, ...]
    first_year: int
    latest_year: int
    year_count: int
    rows_wide: int
    municipalities: int
    biomes: int
    states: int
    classes_in_statistics: tuple[int, ...]
    classes_in_legend: tuple[int, ...]
    classes_statistics_only: tuple[int, ...]
    classes_legend_only: tuple[int, ...]
    duplicate_source_grains: int
    municipalities_in_multiple_biomes: int
    legend_encoding: str
    legend_delimiter: str
    legend_columns: tuple[str, ...]


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def _load_excel_extension(connection: duckdb.DuckDBPyConnection) -> None:
    try:
        connection.execute("LOAD excel")
    except duckdb.Error:
        connection.execute("INSTALL excel")
        connection.execute("LOAD excel")


def workbook_sheet_names(path: Path) -> tuple[str, ...]:
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as workbook:
        root = ElementTree.fromstring(workbook.read("xl/workbook.xml"))
    return tuple(
        sheet.attrib["name"] for sheet in root.findall("x:sheets/x:sheet", namespace)
    )


def inspect_legend_csv(path: Path) -> tuple[str, str, tuple[str, ...]]:
    content = path.read_bytes()
    encoding = "utf-8-sig" if content.startswith(b"\xef\xbb\xbf") else "utf-8"
    text = content.decode(encoding)
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    reader = csv.reader(text.splitlines(), dialect)
    columns = tuple(next(reader))
    expected = ("class_id", "class_name_pt_br", "class_name_en", "hex_code")
    if columns != expected:
        raise RuntimeError(
            f"Schema da legenda MapBiomas mudou: esperado {expected}, recebido {columns}"
        )
    return encoding, dialect.delimiter, columns


def _legend_semantic_id(path: Path, expected_name: str) -> int:
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    matches = [
        int(row["class_id"])
        for row in rows
        if row["class_name_pt_br"].casefold() == expected_name.casefold()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Esperava uma classe oficial {expected_name!r}, encontrei {len(matches)}"
        )
    return matches[0]


def _class_ids_for_branches(
    connection: duckdb.DuckDBPyConnection, branch_names: tuple[str, ...]
) -> tuple[int, ...]:
    placeholders = ", ".join("?" for _ in branch_names)
    rows = connection.execute(
        f"""
        SELECT DISTINCT CAST("class" AS INTEGER)
        FROM raw_mapbiomas_wide
        WHERE class_level_1 IN ({placeholders})
        ORDER BY 1
        """,
        list(branch_names),
    ).fetchall()
    if not rows:
        raise RuntimeError(
            f"Nenhuma classe encontrada para os ramos oficiais {branch_names}"
        )
    return tuple(row[0] for row in rows)


def resolve_class_semantics(
    connection: duckdb.DuckDBPyConnection,
    *,
    legend_path: Path,
    urban_class_id_from_documentation: int,
) -> ClassSemantics:
    urban_class_id = _legend_semantic_id(legend_path, "Área Urbanizada")
    water_class_id = _legend_semantic_id(legend_path, "Rio, Lago e Oceano")
    wetland_class_id = _legend_semantic_id(
        legend_path, "Campo Alagado e Área Pantanosa"
    )
    if urban_class_id != urban_class_id_from_documentation:
        raise RuntimeError(
            "A pagina oficial de urbanizacao e o CSV de legenda discordam sobre "
            "a classe Área Urbanizada"
        )

    distinct_branches = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT class_level_1 FROM raw_mapbiomas_wide"
        ).fetchall()
    }
    native_branches = (
        "1. Forest",
        "2. Herbaceous and Shrubby Vegetation",
    )
    agriculture_branch = ("3. Farming",)
    missing_branches = set(native_branches + agriculture_branch) - distinct_branches
    if missing_branches:
        raise RuntimeError(
            "Hierarquia oficial mudou; ramos sem correspondencia: "
            + ", ".join(sorted(missing_branches))
        )

    native_ids = _class_ids_for_branches(connection, native_branches)
    agriculture_ids = _class_ids_for_branches(connection, agriculture_branch)
    not_observed_rows = connection.execute(
        """
        SELECT DISTINCT CAST("class" AS INTEGER)
        FROM raw_mapbiomas_wide
        WHERE regexp_matches(class_level_1, 'Not Observed', 'i')
        ORDER BY 1
        """
    ).fetchall()
    not_observed_ids = tuple(row[0] for row in not_observed_rows)
    all_source_ids = tuple(
        row[0]
        for row in connection.execute(
            'SELECT DISTINCT CAST("class" AS INTEGER) FROM raw_mapbiomas_wide ORDER BY 1'
        ).fetchall()
    )
    mapped_ids = tuple(
        class_id for class_id in all_source_ids if class_id not in not_observed_ids
    )
    source_ids = set(all_source_ids)
    required_ids = {urban_class_id, water_class_id, wetland_class_id}
    if missing := required_ids - source_ids:
        raise RuntimeError(
            "Classes de indicadores ausentes da tabela estatistica: "
            + ", ".join(map(str, sorted(missing)))
        )
    return ClassSemantics(
        urban_class_id=urban_class_id,
        water_class_id=water_class_id,
        wetland_class_id=wetland_class_id,
        not_observed_class_ids=not_observed_ids,
        native_vegetation_class_ids=native_ids,
        agriculture_livestock_class_ids=agriculture_ids,
        mapped_class_ids=mapped_ids,
    )


def _integer_list_sql(values: tuple[int, ...]) -> str:
    if not values:
        return "NULL"
    return ", ".join(str(value) for value in values)


def create_mapbiomas_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    xlsx_path: Path,
    legend_path: Path,
    dim_municipality_path: Path,
    collection_id: str,
    collection_version: str,
    expected_first_year: int,
    expected_latest_year: int,
    source_filename: str,
    source_sha256: str,
    source_member_sha256: str,
    legend_sha256: str,
    source_url: str,
    source_publication_date: str | None,
    ingested_at: datetime,
    urban_class_id_from_documentation: int,
) -> tuple[SourceInspection, ClassSemantics]:
    if not dim_municipality_path.exists():
        raise RuntimeError(
            f"dim_municipality obrigatoria nao encontrada: {dim_municipality_path}"
        )
    if not zipfile.is_zipfile(xlsx_path):
        raise RuntimeError(f"Planilha XLSX invalida: {xlsx_path}")
    sheet_name = f"COVERAGE_{collection_id}"
    sheets = workbook_sheet_names(xlsx_path)
    if sheet_name not in sheets:
        raise RuntimeError(
            f"A planilha da colecao {collection_id} nao contem a folha {sheet_name}: "
            f"{sheets}"
        )
    legend_encoding, legend_delimiter, legend_columns = inspect_legend_csv(legend_path)
    _load_excel_extension(connection)
    connection.execute(
        f"""
        CREATE TABLE raw_mapbiomas_wide AS
        SELECT *
        FROM read_xlsx(
            '{_sql_path(xlsx_path)}',
            sheet='{sheet_name.replace("'", "''")}',
            header=true
        )
        """
    )
    description = connection.execute("DESCRIBE raw_mapbiomas_wide").fetchall()
    columns = tuple(row[0] for row in description)
    source_columns = tuple((row[0], row[1]) for row in description)
    if columns[: len(EXPECTED_SOURCE_COLUMNS)] != EXPECTED_SOURCE_COLUMNS:
        raise RuntimeError(
            "Schema inicial da tabela estatistica MapBiomas mudou: "
            f"{columns[:len(EXPECTED_SOURCE_COLUMNS)]}"
        )
    year_columns = tuple(column for column in columns if re.fullmatch(r"y\d{4}", column))
    years = tuple(int(column[1:]) for column in year_columns)
    expected_years = tuple(range(expected_first_year, expected_latest_year + 1))
    if years != expected_years:
        raise RuntimeError(
            f"Serie anual da planilha {years} diverge da descoberta {expected_years}"
        )
    unexpected_columns = set(columns) - set(EXPECTED_SOURCE_COLUMNS) - set(year_columns)
    if unexpected_columns:
        raise RuntimeError(
            "Colunas nao reconhecidas na tabela MapBiomas: "
            + ", ".join(sorted(unexpected_columns))
        )

    connection.execute(
        f"""
        CREATE TABLE raw_mapbiomas_legend AS
        SELECT
            CAST(class_id AS INTEGER) AS class_id,
            class_name_pt_br,
            class_name_en,
            hex_code
        FROM read_csv(
            '{_sql_path(legend_path)}',
            header=true,
            delim='{legend_delimiter}',
            encoding='utf-8',
            columns={{
                'class_id': 'INTEGER',
                'class_name_pt_br': 'VARCHAR',
                'class_name_en': 'VARCHAR',
                'hex_code': 'VARCHAR'
            }}
        )
        """
    )
    duplicate_legend_ids = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT class_id FROM raw_mapbiomas_legend
            GROUP BY class_id HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_legend_ids:
        raise RuntimeError("A legenda oficial possui class_id duplicado")

    hierarchy_conflicts = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT "class"
            FROM raw_mapbiomas_wide
            GROUP BY "class"
            HAVING count(DISTINCT struct_pack(
                l0 := class_level_0,
                l1 := class_level_1,
                l2 := class_level_2,
                l3 := class_level_3,
                l4 := class_level_4
            )) <> 1
        )
        """
    ).fetchone()[0]
    if hierarchy_conflicts:
        raise RuntimeError("Uma classe possui mais de uma hierarquia no XLSX oficial")

    semantics = resolve_class_semantics(
        connection,
        legend_path=legend_path,
        urban_class_id_from_documentation=urban_class_id_from_documentation,
    )
    native_ids_sql = _integer_list_sql(semantics.native_vegetation_class_ids)
    agriculture_ids_sql = _integer_list_sql(
        semantics.agriculture_livestock_class_ids
    )
    mapped_ids_sql = _integer_list_sql(semantics.mapped_class_ids)

    connection.execute(
        f"""
        CREATE TABLE mapbiomas_class_legend AS
        WITH hierarchy AS (
            SELECT
                CAST("class" AS INTEGER) AS class_id,
                any_value(class_level_0) AS class_level_0_name,
                any_value(class_level_1) AS class_level_1_name,
                any_value(class_level_2) AS class_level_2_name,
                any_value(class_level_3) AS class_level_3_name,
                any_value(class_level_4) AS class_level_4_name
            FROM raw_mapbiomas_wide
            GROUP BY "class"
        ), combined AS (
            SELECT
                COALESCE(h.class_id, l.class_id) AS class_id,
                l.class_name_pt_br,
                l.class_name_en,
                l.hex_code,
                h.class_level_0_name,
                h.class_level_1_name,
                h.class_level_2_name,
                h.class_level_3_name,
                h.class_level_4_name,
                h.class_id IS NOT NULL AS is_in_statistics,
                l.class_id IS NOT NULL AS is_in_legend_csv
            FROM hierarchy h
            FULL JOIN raw_mapbiomas_legend l USING (class_id)
        )
        SELECT
            '{collection_id.replace("'", "''")}'::VARCHAR AS collection_id,
            '{collection_version.replace("'", "''")}'::VARCHAR AS collection_version,
            class_id,
            COALESCE(
                class_name_pt_br,
                regexp_replace(class_level_4_name, '^[0-9.]+\\s*', '')
            ) AS class_name,
            class_name_pt_br,
            class_name_en,
            hex_code,
            CASE
                WHEN class_level_4_name IS DISTINCT FROM class_level_3_name THEN 4
                WHEN class_level_3_name IS DISTINCT FROM class_level_2_name THEN 3
                WHEN class_level_2_name IS DISTINCT FROM class_level_1_name THEN 2
                WHEN class_level_1_name IS NOT NULL THEN 1
            END::INTEGER AS class_level,
            class_level_0_name,
            class_level_1_name,
            class_level_2_name,
            class_level_3_name,
            class_level_4_name,
            is_in_statistics,
            is_in_legend_csv,
            class_id IN ({mapped_ids_sql}) AS is_mapped_class,
            class_id IN ({native_ids_sql}) AS is_native_vegetation,
            class_id IN ({agriculture_ids_sql}) AS is_agriculture_livestock,
            CASE
                WHEN is_in_legend_csv THEN 'official_legend_csv'
                ELSE 'statistics_workbook_hierarchy'
            END AS class_name_source,
            '{source_sha256}'::VARCHAR AS statistics_source_sha256,
            '{legend_sha256}'::VARCHAR AS legend_source_sha256,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM combined
        ORDER BY class_id
        """
    )

    year_column_sql = ", ".join(f'"{column}"' for column in year_columns)
    source_publication_sql = (
        f"DATE '{source_publication_date}'"
        if source_publication_date
        else "NULL::DATE"
    )
    connection.execute(
        f"""
        CREATE TABLE silver_mapbiomas_land_cover AS
        WITH long_source AS (
            SELECT
                country,
                biome,
                region,
                state,
                geocode,
                municipality,
                CAST("class" AS INTEGER) AS class_id,
                CAST(substr(year_name, 2) AS INTEGER) AS year,
                area_ha
            FROM (
                UNPIVOT raw_mapbiomas_wide
                ON {year_column_sql}
                INTO NAME year_name VALUE area_ha
            )
        ), normalized AS (
            SELECT
                '{collection_id.replace("'", "''")}'::VARCHAR AS collection_id,
                '{collection_version.replace("'", "''")}'::VARCHAR AS collection_version,
                s.geocode::VARCHAR AS codigo_ibge,
                NULL::VARCHAR AS biome_code,
                s.biome::VARCHAR AS biome_name,
                s.year::INTEGER AS year,
                s.class_id::INTEGER AS class_id,
                l.class_name,
                l.class_level,
                l.class_level_0_name,
                l.class_level_1_name,
                l.class_level_2_name,
                l.class_level_3_name,
                l.class_level_4_name,
                l.is_mapped_class,
                l.is_native_vegetation,
                l.is_agriculture_livestock,
                sum(s.area_ha)::DOUBLE AS area_ha,
                any_value(s.municipality)::VARCHAR AS municipality_name_source,
                list_sort(list_distinct(list(s.region))) AS source_region_names,
                list_sort(list_distinct(list(s.state))) AS source_state_names,
                count(*)::INTEGER AS source_row_count,
                d.codigo_ibge IS NOT NULL AS is_dim_municipality_match,
                '{source_filename.replace("'", "''")}'::VARCHAR AS source_filename,
                '{source_sha256}'::VARCHAR AS source_sha256,
                '{source_member_sha256}'::VARCHAR AS source_member_sha256,
                '{source_url.replace("'", "''")}'::VARCHAR AS source_url,
                {source_publication_sql} AS source_publication_date,
                TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
            FROM long_source s
            JOIN mapbiomas_class_legend l USING (class_id)
            LEFT JOIN read_parquet('{_sql_path(dim_municipality_path)}') d
                ON s.geocode = d.codigo_ibge
            GROUP BY ALL
        )
        SELECT * FROM normalized
        ORDER BY codigo_ibge, biome_name, year, class_id
        """
    )

    connection.execute(
        """
        CREATE TABLE fact_municipality_land_cover AS
        SELECT
            codigo_ibge,
            year,
            class_id,
            any_value(class_name)::VARCHAR AS class_name,
            any_value(class_level)::INTEGER AS class_level,
            sum(area_ha)::DOUBLE AS area_ha,
            (sum(area_ha) / 100.0)::DOUBLE AS area_km2,
            any_value(collection_id)::VARCHAR AS collection_id,
            any_value(collection_version)::VARCHAR AS collection_version,
            any_value(source_sha256)::VARCHAR AS source_sha256,
            any_value(source_publication_date)::DATE AS source_publication_date,
            any_value(ingested_at)::TIMESTAMPTZ AS ingested_at
        FROM silver_mapbiomas_land_cover
        WHERE is_dim_municipality_match
        GROUP BY codigo_ibge, year, class_id
        ORDER BY codigo_ibge, year, class_id
        """
    )

    connection.execute(
        f"""
        CREATE TABLE snapshot_municipality_land_cover AS
        WITH areas AS (
            SELECT
                codigo_ibge,
                year,
                sum(area_ha) FILTER (WHERE is_mapped_class)::DOUBLE AS mapped_area_ha,
                coalesce(sum(area_ha) FILTER (
                    WHERE class_id = {semantics.urban_class_id}
                ), 0.0)::DOUBLE AS urban_area_ha,
                coalesce(sum(area_ha) FILTER (
                    WHERE is_native_vegetation
                ), 0.0)::DOUBLE AS native_vegetation_area_ha,
                coalesce(sum(area_ha) FILTER (
                    WHERE is_agriculture_livestock
                ), 0.0)::DOUBLE AS agriculture_livestock_area_ha,
                coalesce(sum(area_ha) FILTER (
                    WHERE class_id = {semantics.water_class_id}
                ), 0.0)::DOUBLE AS water_area_ha,
                coalesce(sum(area_ha) FILTER (
                    WHERE class_id = {semantics.wetland_class_id}
                ), 0.0)::DOUBLE AS wetland_area_ha,
                any_value(collection_id)::VARCHAR AS collection_id,
                any_value(collection_version)::VARCHAR AS collection_version,
                any_value(source_sha256)::VARCHAR AS source_sha256,
                any_value(source_publication_date)::DATE AS source_publication_date,
                any_value(ingested_at)::TIMESTAMPTZ AS ingested_at
            FROM silver_mapbiomas_land_cover
            WHERE is_dim_municipality_match
            GROUP BY codigo_ibge, year
        )
        SELECT
            codigo_ibge,
            year,
            mapped_area_ha,
            urban_area_ha,
            urban_area_ha / 100.0 AS urban_area_km2,
            urban_area_ha / nullif(mapped_area_ha, 0) * 100.0 AS urban_area_pct,
            native_vegetation_area_ha,
            native_vegetation_area_ha / 100.0 AS native_vegetation_area_km2,
            native_vegetation_area_ha / nullif(mapped_area_ha, 0) * 100.0
                AS native_vegetation_area_pct,
            agriculture_livestock_area_ha,
            agriculture_livestock_area_ha / 100.0
                AS agriculture_livestock_area_km2,
            agriculture_livestock_area_ha / nullif(mapped_area_ha, 0) * 100.0
                AS agriculture_livestock_area_pct,
            water_area_ha,
            water_area_ha / 100.0 AS water_area_km2,
            water_area_ha / nullif(mapped_area_ha, 0) * 100.0 AS water_area_pct,
            wetland_area_ha,
            wetland_area_ha / 100.0 AS wetland_area_km2,
            wetland_area_ha / nullif(mapped_area_ha, 0) * 100.0 AS wetland_area_pct,
            collection_id,
            collection_version,
            source_sha256,
            source_publication_date,
            ingested_at
        FROM areas
        ORDER BY codigo_ibge, year
        """
    )

    connection.execute(
        f"""
        CREATE TABLE municipality_land_cover_change AS
        WITH bounds AS (
            SELECT min(year)::INTEGER AS first_year, max(year)::INTEGER AS latest_year
            FROM snapshot_municipality_land_cover
        ), joined AS (
            SELECT
                latest.codigo_ibge,
                bounds.first_year,
                bounds.latest_year,
                bounds.latest_year - 5 AS reference_year_5y,
                bounds.latest_year - 10 AS reference_year_10y,
                bounds.latest_year - 20 AS reference_year_20y,
                first.urban_area_ha AS urban_area_first_year_ha,
                latest.urban_area_ha AS urban_area_latest_year_ha,
                y5.urban_area_ha AS urban_area_5y_reference_ha,
                y10.urban_area_ha AS urban_area_10y_reference_ha,
                y20.urban_area_ha AS urban_area_20y_reference_ha,
                first.native_vegetation_area_ha
                    AS native_vegetation_first_year_ha,
                latest.native_vegetation_area_ha
                    AS native_vegetation_latest_year_ha,
                y5.native_vegetation_area_ha
                    AS native_vegetation_5y_reference_ha,
                y10.native_vegetation_area_ha
                    AS native_vegetation_10y_reference_ha,
                y20.native_vegetation_area_ha
                    AS native_vegetation_20y_reference_ha,
                y10.water_area_ha AS water_area_10y_reference_ha,
                latest.water_area_ha AS water_area_latest_year_ha,
                y10.wetland_area_ha AS wetland_area_10y_reference_ha,
                latest.wetland_area_ha AS wetland_area_latest_year_ha,
                latest.collection_id,
                latest.collection_version,
                latest.source_sha256,
                latest.source_publication_date,
                latest.ingested_at
            FROM snapshot_municipality_land_cover latest
            CROSS JOIN bounds
            JOIN snapshot_municipality_land_cover first
                ON first.codigo_ibge = latest.codigo_ibge
               AND first.year = bounds.first_year
            JOIN snapshot_municipality_land_cover y5
                ON y5.codigo_ibge = latest.codigo_ibge
               AND y5.year = bounds.latest_year - 5
            JOIN snapshot_municipality_land_cover y10
                ON y10.codigo_ibge = latest.codigo_ibge
               AND y10.year = bounds.latest_year - 10
            JOIN snapshot_municipality_land_cover y20
                ON y20.codigo_ibge = latest.codigo_ibge
               AND y20.year = bounds.latest_year - 20
            WHERE latest.year = bounds.latest_year
        )
        SELECT
            codigo_ibge,
            first_year,
            latest_year,
            reference_year_5y,
            reference_year_10y,
            reference_year_20y,
            urban_area_first_year_ha,
            urban_area_latest_year_ha,
            urban_area_latest_year_ha - urban_area_first_year_ha
                AS urban_area_change_ha,
            (urban_area_latest_year_ha - urban_area_first_year_ha)
                / nullif(urban_area_first_year_ha, 0) * 100.0
                AS urban_area_change_pct,
            urban_area_latest_year_ha - urban_area_5y_reference_ha
                AS urban_change_5y_ha,
            (urban_area_latest_year_ha - urban_area_5y_reference_ha)
                / nullif(urban_area_5y_reference_ha, 0) * 100.0
                AS urban_change_5y_pct,
            urban_area_latest_year_ha - urban_area_10y_reference_ha
                AS urban_change_10y_ha,
            (urban_area_latest_year_ha - urban_area_10y_reference_ha)
                / nullif(urban_area_10y_reference_ha, 0) * 100.0
                AS urban_change_10y_pct,
            urban_area_latest_year_ha - urban_area_20y_reference_ha
                AS urban_change_20y_ha,
            (urban_area_latest_year_ha - urban_area_20y_reference_ha)
                / nullif(urban_area_20y_reference_ha, 0) * 100.0
                AS urban_change_20y_pct,
            native_vegetation_first_year_ha,
            native_vegetation_latest_year_ha,
            native_vegetation_latest_year_ha - native_vegetation_first_year_ha
                AS native_vegetation_change_ha,
            (native_vegetation_latest_year_ha - native_vegetation_first_year_ha)
                / nullif(native_vegetation_first_year_ha, 0) * 100.0
                AS native_vegetation_change_pct,
            native_vegetation_latest_year_ha
                - native_vegetation_5y_reference_ha
                AS native_vegetation_change_5y_ha,
            (native_vegetation_latest_year_ha
                - native_vegetation_5y_reference_ha)
                / nullif(native_vegetation_5y_reference_ha, 0) * 100.0
                AS native_vegetation_change_5y_pct,
            native_vegetation_latest_year_ha
                - native_vegetation_10y_reference_ha
                AS native_vegetation_change_10y_ha,
            (native_vegetation_latest_year_ha
                - native_vegetation_10y_reference_ha)
                / nullif(native_vegetation_10y_reference_ha, 0) * 100.0
                AS native_vegetation_change_10y_pct,
            native_vegetation_latest_year_ha
                - native_vegetation_20y_reference_ha
                AS native_vegetation_change_20y_ha,
            (native_vegetation_latest_year_ha
                - native_vegetation_20y_reference_ha)
                / nullif(native_vegetation_20y_reference_ha, 0) * 100.0
                AS native_vegetation_change_20y_pct,
            water_area_latest_year_ha - water_area_10y_reference_ha
                AS water_area_change_10y_ha,
            wetland_area_latest_year_ha - wetland_area_10y_reference_ha
                AS wetland_area_change_10y_ha,
            collection_id,
            collection_version,
            source_sha256,
            source_publication_date,
            ingested_at
        FROM joined
        ORDER BY codigo_ibge
        """
    )

    stats_class_ids = tuple(
        row[0]
        for row in connection.execute(
            'SELECT DISTINCT CAST("class" AS INTEGER) FROM raw_mapbiomas_wide ORDER BY 1'
        ).fetchall()
    )
    legend_class_ids = tuple(
        row[0]
        for row in connection.execute(
            "SELECT class_id FROM raw_mapbiomas_legend ORDER BY class_id"
        ).fetchall()
    )
    inspection = SourceInspection(
        format="ZIP containing XLSX (Office Open XML)",
        workbook_sheets=sheets,
        source_columns=source_columns,
        year_columns=year_columns,
        first_year=min(years),
        latest_year=max(years),
        year_count=len(years),
        rows_wide=connection.execute(
            "SELECT count(*) FROM raw_mapbiomas_wide"
        ).fetchone()[0],
        municipalities=connection.execute(
            "SELECT count(DISTINCT geocode) FROM raw_mapbiomas_wide"
        ).fetchone()[0],
        biomes=connection.execute(
            "SELECT count(DISTINCT biome) FROM raw_mapbiomas_wide"
        ).fetchone()[0],
        states=connection.execute(
            "SELECT count(DISTINCT state) FROM raw_mapbiomas_wide"
        ).fetchone()[0],
        classes_in_statistics=stats_class_ids,
        classes_in_legend=legend_class_ids,
        classes_statistics_only=tuple(sorted(set(stats_class_ids) - set(legend_class_ids))),
        classes_legend_only=tuple(sorted(set(legend_class_ids) - set(stats_class_ids))),
        duplicate_source_grains=connection.execute(
            """
            SELECT count(*) FROM (
                SELECT geocode, biome, "class"
                FROM raw_mapbiomas_wide
                GROUP BY ALL HAVING count(*) > 1
            )
            """
        ).fetchone()[0],
        municipalities_in_multiple_biomes=connection.execute(
            """
            SELECT count(*) FROM (
                SELECT geocode FROM raw_mapbiomas_wide
                GROUP BY geocode HAVING count(DISTINCT biome) > 1
            )
            """
        ).fetchone()[0],
        legend_encoding=legend_encoding,
        legend_delimiter=legend_delimiter,
        legend_columns=legend_columns,
    )
    return inspection, semantics


def _copy_atomically(
    connection: duckdb.DuckDBPyConnection,
    *,
    table: str,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()
    connection.execute(
        f"COPY {table} TO '{_sql_path(temporary_path)}' "
        "(FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    temporary_path.replace(destination)


def write_mapbiomas_artifacts(
    connection: duckdb.DuckDBPyConnection,
    *,
    silver_path: Path,
    class_legend_path: Path,
    fact_path: Path,
    snapshot_path: Path,
    change_path: Path,
) -> None:
    for table, destination in (
        ("silver_mapbiomas_land_cover", silver_path),
        ("mapbiomas_class_legend", class_legend_path),
        ("fact_municipality_land_cover", fact_path),
        ("snapshot_municipality_land_cover", snapshot_path),
        ("municipality_land_cover_change", change_path),
    ):
        _copy_atomically(connection, table=table, destination=destination)
