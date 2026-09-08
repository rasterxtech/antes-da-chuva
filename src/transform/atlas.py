from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

import duckdb

from src.contracts.atlas import (
    COUNT_FIELDS,
    MONETARY_FIELDS,
    required_fields,
    validate_fields,
)


CLASSIFICATION_VERSION = "atlas_cobrade_rain_v1"
RAIN_RELATED_CODES = (
    "11311",
    "11312",
    "11313",
    "11314",
    "11321",
    "11331",
    "11332",
    "11340",
    "12100",
    "12200",
    "12300",
    "13214",
)
ENVIRONMENT_FIELDS = (
    "DA_Polui/cont da água",
    "DA_Polui/cont do ar",
    "DA_Polui/cont do solo",
    "DA_Dimi/exauri hídrico",
    "DA_Incêndi parques/APA's/APP's",
)


@dataclass(frozen=True)
class SourceInspection:
    format: str
    encoding: str
    delimiter: str
    quote_character: str
    line_ending: str
    columns: tuple[str, ...]
    column_count: int
    rows: int
    physical_lines: int
    workbook_sheets: tuple[str, ...]
    workbook_source_columns: tuple[tuple[str, str], ...]
    correction_log_sheets: tuple[str, ...]
    first_event_date: str
    latest_event_date: str
    first_registration_date: str
    latest_registration_date: str
    municipality_count: int
    cobrade_count_observed: int
    cobrade_count_dimension: int
    correction_reference_year: int
    correction_reference_index: float


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def _sql_text(value: str) -> str:
    return value.replace("'", "''")


def _sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


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


def workbook_sheet_dimensions(path: Path) -> dict[str, str]:
    spreadsheet = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    document_relationship = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    )
    package_relationship = "http://schemas.openxmlformats.org/package/2006/relationships"
    with zipfile.ZipFile(path) as workbook:
        root = ElementTree.fromstring(workbook.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            workbook.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall(f"{{{package_relationship}}}Relationship")
        }
        dimensions = {}
        for sheet in root.findall(f"{{{spreadsheet}}}sheets/{{{spreadsheet}}}sheet"):
            target = targets[sheet.attrib[f"{{{document_relationship}}}id"]]
            member = target.lstrip("/")
            if not member.startswith("xl/"):
                member = "xl/" + member
            worksheet = ElementTree.fromstring(workbook.read(member))
            dimension = worksheet.find(f"{{{spreadsheet}}}dimension")
            if dimension is None or "ref" not in dimension.attrib:
                raise RuntimeError(f"Folha XLSX sem dimensao declarada: {sheet.attrib['name']}")
            dimensions[sheet.attrib["name"]] = dimension.attrib["ref"]
    return dimensions


def inspect_csv_header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="cp1252", newline="") as source:
        observed = tuple(next(csv.reader(source, delimiter=";", quotechar='"')))
    validate_fields(observed)
    return observed


def _count(column: str, alias: str) -> str:
    return f'CAST(trim("{column}") AS BIGINT) AS {alias}'


def _money(column: str, alias: str) -> str:
    return f'CAST(trim("{column}") AS DECIMAL(38,2)) AS {alias}'


def _code_list_sql(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def _corrected_workbook_field_comparisons() -> dict[str, str]:
    comparisons = {}
    for field in required_fields:
        identifier = _sql_identifier(field)
        csv_value = f"c.{identifier}"
        workbook_value = f"x.{identifier}"
        if field in {"Data_Registro", "Data_Evento"}:
            comparison = (
                f"strptime(trim({csv_value}), '%d/%m/%Y')::DATE "
                f"IS NOT DISTINCT FROM DATE '1899-12-30' "
                f"+ CAST(floor(CAST({workbook_value} AS DOUBLE)) AS INTEGER)"
            )
        elif field in {"Cod_Cobrade", "Cod_IBGE_Mun"}:
            comparison = (
                f"trim({csv_value}) IS NOT DISTINCT FROM "
                f"CAST(CAST({workbook_value} AS BIGINT) AS VARCHAR)"
            )
        elif field in COUNT_FIELDS:
            comparison = (
                f"try_cast(nullif(trim({csv_value}), '') AS BIGINT) "
                f"IS NOT DISTINCT FROM CAST(round(try_cast({workbook_value} AS DOUBLE), 0) "
                f"AS BIGINT)"
            )
        elif field in MONETARY_FIELDS:
            comparison = (
                f"try_cast(nullif(trim({csv_value}), '') AS DECIMAL(38,2)) "
                f"IS NOT DISTINCT FROM CAST(round(try_cast({workbook_value} AS DOUBLE), 2) "
                f"AS DECIMAL(38,2))"
            )
        elif field == "tipologia" or field in ENVIRONMENT_FIELDS:
            comparison = (
                f"try_cast(nullif(trim({csv_value}), '') AS DOUBLE) "
                f"IS NOT DISTINCT FROM try_cast({workbook_value} AS DOUBLE)"
            )
        else:
            comparison = (
                f"coalesce({csv_value}, '') = "
                f"coalesce(replace(replace(CAST({workbook_value} AS VARCHAR), "
                f"'_x000D_', ''), '_x0002_', chr(2)), '')"
            )
        comparisons[field] = comparison
    return comparisons


def _corrected_workbook_match_expression() -> str:
    return " AND ".join(
        f"({comparison})"
        for comparison in _corrected_workbook_field_comparisons().values()
    )


def create_atlas_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    csv_path: Path,
    xlsx_path: Path,
    correction_log_path: Path,
    manual_path: Path,
    dim_municipality_path: Path,
    source_release: str,
    source_url: str,
    source_official_date: str,
    csv_sha256: str,
    xlsx_sha256: str,
    correction_log_sha256: str,
    manual_sha256: str,
    ingested_at: datetime,
) -> SourceInspection:
    if not dim_municipality_path.exists():
        raise RuntimeError(
            f"dim_municipality obrigatoria nao encontrada: {dim_municipality_path}"
        )
    columns = inspect_csv_header(csv_path)
    if not zipfile.is_zipfile(xlsx_path):
        raise RuntimeError(f"Base Atlas XLSX invalida: {xlsx_path}")
    if not zipfile.is_zipfile(correction_log_path):
        raise RuntimeError(f"Log de correcoes Atlas XLSX invalido: {correction_log_path}")
    if not manual_path.read_bytes()[:5] == b"%PDF-":
        raise RuntimeError(f"Manual Atlas PDF invalido: {manual_path}")
    sheets = workbook_sheet_names(xlsx_path)
    sheet_dimensions = workbook_sheet_dimensions(xlsx_path)
    correction_log_sheets = workbook_sheet_names(correction_log_path)
    required_sheets = {
        "Atlas Valores Originais",
        "Cálculo Correção",
        "Atlas Valores Corrigidos",
        "Grupos de Desastres",
    }
    if missing := required_sheets - set(sheets):
        raise RuntimeError(f"Folhas obrigatorias ausentes no XLSX Atlas: {sorted(missing)}")
    required_log_sheets = {
        "Lista",
        "População",
        "Protocolos Corrigidos",
        "Protocolos não relacionados",
    }
    if missing := required_log_sheets - set(correction_log_sheets):
        raise RuntimeError(
            f"Folhas obrigatorias ausentes no log Atlas: {sorted(missing)}"
        )

    connection.execute("SET preserve_insertion_order=true")
    connection.execute(
        f"""
        CREATE TABLE raw_atlas_event AS
        SELECT row_number() OVER ()::BIGINT AS source_row_number, *
        FROM read_csv(
            '{_sql_path(csv_path)}',
            delim=';',
            quote='"',
            header=true,
            all_varchar=true,
            encoding='CP1252',
            strict_mode=true,
            sample_size=-1,
            nullstr='__ATLAS_VALUE_THAT_IS_NEVER_NULL__'
        )
        """
    )
    observed_columns = tuple(
        row[0]
        for row in connection.execute("DESCRIBE raw_atlas_event").fetchall()
        if row[0] != "source_row_number"
    )
    validate_fields(observed_columns)

    _load_excel_extension(connection)
    workbook_descriptions = {}
    for sheet in ("Atlas Valores Originais", "Atlas Valores Corrigidos"):
        description = connection.execute(
            f"DESCRIBE SELECT * FROM read_xlsx('{_sql_path(xlsx_path)}', "
            f"sheet='{sheet}', header=true)"
        ).fetchall()
        workbook_descriptions[sheet] = tuple((row[0], row[1]) for row in description)
        validate_fields(tuple(row[0] for row in description))
    event_rows = connection.execute("SELECT count(*) FROM raw_atlas_event").fetchone()[0]
    for sheet in ("Atlas Valores Originais", "Atlas Valores Corrigidos"):
        row_match = re.search(r"(\d+)$", sheet_dimensions[sheet])
        if not row_match or int(row_match.group(1)) != event_rows + 1:
            raise RuntimeError(
                f"Dimensao inesperada na folha {sheet}: {sheet_dimensions[sheet]}"
            )
    id_range = f"A1:A{event_rows + 1}"
    connection.execute(
        f"""
        CREATE TABLE raw_atlas_original_workbook_ids AS
        SELECT Protocolo_S2iD::VARCHAR AS source_event_id
        FROM read_xlsx(
            '{_sql_path(xlsx_path)}',
            sheet='Atlas Valores Originais',
            range='{id_range}',
            header=true
        )
        """
    )
    connection.execute(
        f"""
        CREATE TABLE raw_atlas_corrected_workbook AS
        SELECT *
        FROM read_xlsx(
            '{_sql_path(xlsx_path)}',
            sheet='Atlas Valores Corrigidos',
            header=true,
            all_varchar=true
        )
        """
    )
    connection.execute(
        """
        CREATE VIEW raw_atlas_corrected_workbook_ids AS
        SELECT Protocolo_S2iD::VARCHAR AS source_event_id
        FROM raw_atlas_corrected_workbook
        """
    )
    workbook_match_expression = _corrected_workbook_match_expression()
    connection.execute(
        f"""
        CREATE TABLE raw_atlas_corrected_workbook_comparison AS
        SELECT
            c.Protocolo_S2iD::VARCHAR AS source_event_id,
            {workbook_match_expression} AS all_fields_match
        FROM raw_atlas_event c
        JOIN raw_atlas_corrected_workbook x USING (Protocolo_S2iD)
        """
    )
    connection.execute(
        f"""
        CREATE TABLE dim_disaster_type AS
        SELECT
            lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0')
                AS cobrade_code,
            Desastre::VARCHAR AS disaster_name,
            "Atlas - Descrição Tipologia"::VARCHAR AS atlas_type_name,
            CAST("Atlas N. Tipologia" AS SMALLINT) AS atlas_type_id,
            "Grupo de desastres"::VARCHAR AS atlas_group_name,
            substr(lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0'), 1, 1)
                AS cobrade_category_code,
            substr(lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0'), 1, 2)
                AS cobrade_group_code,
            substr(lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0'), 1, 3)
                AS cobrade_subgroup_code,
            substr(lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0'), 1, 2)
                = '12' AS is_hydrological,
            substr(lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0'), 1, 2)
                = '11' AS is_geological,
            lpad(CAST(CAST(Cobrade AS INTEGER) AS VARCHAR), 5, '0') IN
                ({_code_list_sql(RAIN_RELATED_CODES)}) AS is_rain_related,
            '{CLASSIFICATION_VERSION}'::VARCHAR AS classification_version,
            '{_sql_text(source_release)}'::VARCHAR AS source_release,
            '{xlsx_sha256}'::VARCHAR AS source_sha256,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM read_xlsx(
            '{_sql_path(xlsx_path)}',
            sheet='Grupos de Desastres',
            header=true
        )
        WHERE Cobrade IS NOT NULL
        ORDER BY cobrade_code
        """
    )
    duplicate_cobrade = connection.execute(
        """
        SELECT count(*) FROM (
            SELECT cobrade_code FROM dim_disaster_type
            GROUP BY cobrade_code HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_cobrade:
        raise RuntimeError("A dimensao COBRADE oficial possui codigos duplicados")

    connection.execute(
        f"""
        CREATE TABLE atlas_monetary_correction_factor AS
        SELECT
            CAST("Ano Ref" AS SMALLINT) AS reference_year,
            try_cast("igp-di (dezembro)" AS DOUBLE) AS igp_di_december_index,
            CAST("fator para conversão - valores de dezembro de 2024" AS DOUBLE)
                AS correction_factor,
            'IGP-DI'::VARCHAR AS correction_index,
            '{_sql_text(source_release)}'::VARCHAR AS source_release,
            '{xlsx_sha256}'::VARCHAR AS source_sha256,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM read_xlsx(
            '{_sql_path(xlsx_path)}',
            sheet='Cálculo Correção',
            range='B2:F38',
            header=true
        )
        WHERE "Ano Ref" IS NOT NULL
        ORDER BY reference_year
        """
    )
    correction_reference = connection.execute(
        """
        SELECT reference_year, igp_di_december_index
        FROM atlas_monetary_correction_factor
        WHERE correction_factor = 1
        ORDER BY reference_year DESC
        LIMIT 1
        """
    ).fetchone()
    if not correction_reference or correction_reference[1] is None:
        raise RuntimeError("Referencia monetaria IGP-DI nao identificada no XLSX Atlas")
    correction_reference_year = int(correction_reference[0])
    correction_reference_index = float(correction_reference[1])

    source_official_date_sql = f"DATE '{source_official_date}'"
    rain_codes_sql = _code_list_sql(RAIN_RELATED_CODES)
    connection.execute(
        f"""
        CREATE TABLE silver_disaster_event AS
        SELECT
            r.Protocolo_S2iD::VARCHAR AS source_event_id,
            r.Cod_IBGE_Mun::VARCHAR AS codigo_ibge,
            r.Nome_Municipio::VARCHAR AS municipality_name_source,
            r.Sigla_UF::VARCHAR AS uf_code_source,
            r.regiao::VARCHAR AS region_name_source,
            strptime(trim(r.Data_Registro), '%d/%m/%Y')::DATE AS registration_date,
            strptime(trim(r.Data_Evento), '%d/%m/%Y')::DATE AS event_date,
            year(strptime(trim(r.Data_Evento), '%d/%m/%Y'))::SMALLINT AS event_year,
            month(strptime(trim(r.Data_Evento), '%d/%m/%Y'))::TINYINT AS event_month,
            r.Cod_Cobrade::VARCHAR AS cobrade_code,
            CAST(CAST(trim(r.tipologia) AS DOUBLE) AS SMALLINT) AS atlas_type_id,
            r.descricao_tipologia::VARCHAR AS atlas_type_name_source,
            r.grupo_de_desastre::VARCHAR AS atlas_group_name_source,
            nullif(r."Setores Censitários", '')::VARCHAR AS census_sectors_source,
            r.Status::VARCHAR AS status_source,
            r.Status = 'Reconhecido' AS is_federally_recognized,
            nullif(r.DH_Descricao, '')::VARCHAR AS human_damage_description,
            {_count('DH_MORTOS', 'deaths')},
            {_count('DH_FERIDOS', 'injured')},
            {_count('DH_ENFERMOS', 'ill')},
            {_count('DH_DESABRIGADOS', 'homeless')},
            {_count('DH_DESALOJADOS', 'displaced')},
            {_count('DH_DESAPARECIDOS', 'missing')},
            {_count('DH_AFETADOS_SECA_ESTIAGEM', 'drought_affected')},
            {_count('DH_total_danos_humanos_diretos', 'direct_human_damage_total')},
            {_count('DH_OUTROS AFETADOS', 'other_affected')},
            (CAST(trim(r.DH_total_danos_humanos_diretos) AS BIGINT)
                + CAST(trim(r."DH_OUTROS AFETADOS") AS BIGINT))::BIGINT
                AS reported_affected_total,
            nullif(r.DM_Descricao, '')::VARCHAR AS material_damage_description,
            {_count('DM_Uni Habita Danificadas', 'housing_units_damaged')},
            {_count('DM_Uni Habita Destruidas', 'housing_units_destroyed')},
            {_money('DM_Uni Habita Valor', 'housing_damage_brl')},
            {_count('DM_Inst Saúde Danificadas', 'health_facilities_damaged')},
            {_count('DM_Inst Saúde Destruidas', 'health_facilities_destroyed')},
            {_money('DM_Inst Saúde Valor', 'health_facilities_damage_brl')},
            {_count('DM_Inst Ensino Danificadas', 'education_facilities_damaged')},
            {_count('DM_Inst Ensino Destruidas', 'education_facilities_destroyed')},
            {_money('DM_Inst Ensino Valor', 'education_facilities_damage_brl')},
            {_count('DM_Inst Serviços Danificadas', 'service_facilities_damaged')},
            {_count('DM_Inst Serviços Destruidas', 'service_facilities_destroyed')},
            {_money('DM_Inst Serviços Valor', 'service_facilities_damage_brl')},
            {_count('DM_Inst Comuni Danificadas', 'community_facilities_damaged')},
            {_count('DM_Inst Comuni Destruidas', 'community_facilities_destroyed')},
            {_money('DM_Inst Comuni Valor', 'community_facilities_damage_brl')},
            {_count('DM_Obras de Infra Danificadas', 'infrastructure_works_damaged')},
            {_count('DM_Obras de Infra Destruidas', 'infrastructure_works_destroyed')},
            {_money('DM_Obras de Infra Valor', 'infrastructure_damage_brl')},
            {_money('DM_total_danos_materiais', 'material_damage_total_brl')},
            nullif(r.DA_Descricao, '')::VARCHAR AS environmental_damage_description,
            r."DA_Polui/cont da água"::VARCHAR AS water_pollution_impact_source,
            r."DA_Polui/cont do ar"::VARCHAR AS air_pollution_impact_source,
            r."DA_Polui/cont do solo"::VARCHAR AS soil_pollution_impact_source,
            r."DA_Dimi/exauri hídrico"::VARCHAR AS water_depletion_impact_source,
            r."DA_Incêndi parques/APA's/APP's"::VARCHAR AS protected_area_fire_impact_source,
            nullif(r.PEPL_Descricao, '')::VARCHAR AS public_loss_description,
            {_money('PEPL_Assis_méd e emergên(R$)', 'public_health_emergency_loss_brl')},
            {_money('PEPL_Abast de água pot(R$)', 'public_water_supply_loss_brl')},
            {_money('PEPL_sist de esgotos sanit(R$)', 'public_sewerage_loss_brl')},
            {_money('PEPL_Sis limp e rec lixo (R$)', 'public_waste_management_loss_brl')},
            {_money('PEPL_Sis cont pragas (R$)', 'public_pest_control_loss_brl')},
            {_money('PEPL_distrib energia (R$)', 'public_energy_distribution_loss_brl')},
            {_money('PEPL_Telecomunicações (R$)', 'public_telecommunications_loss_brl')},
            {_money('PEPL_Tran loc/reg/l_curso (R$)', 'public_transport_loss_brl')},
            {_money('PEPL_Distrib combustíveis(R$)', 'public_fuel_distribution_loss_brl')},
            {_money('PEPL_Segurança pública (R$)', 'public_safety_loss_brl')},
            {_money('PEPL_Ensino (R$)', 'public_education_loss_brl')},
            {_money('PEPL_total_publico', 'public_loss_total_brl')},
            nullif(r.PEPR_Descricao, '')::VARCHAR AS private_loss_description,
            {_money('PEPR_Agricultura (R$)', 'private_agriculture_loss_brl')},
            {_money('PEPR_Pecuária (R$)', 'private_livestock_loss_brl')},
            {_money('PEPR_Indústria (R$)', 'private_industry_loss_brl')},
            {_money('PEPR_Comércio (R$)', 'private_commerce_loss_brl')},
            {_money('PEPR_Serviços (R$)', 'private_services_loss_brl')},
            {_money('PEPR_total_privado', 'private_loss_total_brl')},
            {_money('PE_PLePR', 'public_private_loss_total_brl')},
            r.Cod_Cobrade IN ({rain_codes_sql}) AS is_rain_related,
            substr(r.Cod_Cobrade, 1, 2) = '12' AS is_hydrological,
            substr(r.Cod_Cobrade, 1, 2) = '11' AS is_geological,
            '{CLASSIFICATION_VERSION}'::VARCHAR AS classification_version,
            regexp_full_match(
                r.Protocolo_S2iD,
                '[A-Z]{{2}}-[A-Z]-[0-9]{{7}}-[0-9]{{5}}-[0-9]{{8}}'
            ) AS is_protocol_format_valid,
            split_part(r.Protocolo_S2iD, '-', 3) = r.Cod_IBGE_Mun
                AS is_protocol_ibge_consistent,
            split_part(r.Protocolo_S2iD, '-', 4) = r.Cod_Cobrade
                AS is_protocol_cobrade_consistent,
            strptime(trim(r.Data_Evento), '%d/%m/%Y')
                > strptime(trim(r.Data_Registro), '%d/%m/%Y')
                AS is_event_after_registration,
            d.codigo_ibge IS NOT NULL AS is_dim_municipality_match,
            true AS monetary_values_are_corrected,
            'IGP-DI'::VARCHAR AS monetary_correction_index,
            {correction_reference_year}::SMALLINT AS monetary_reference_year,
            {_money('DM_total_danos_materiais', 'source_corrected_material_damage_total_brl')},
            '{_sql_text(source_release)}'::VARCHAR AS source_release,
            {source_official_date_sql} AS source_official_date,
            '{csv_sha256}'::VARCHAR AS source_sha256,
            '{xlsx_sha256}'::VARCHAR AS source_workbook_sha256,
            '{correction_log_sha256}'::VARCHAR AS correction_log_sha256,
            '{manual_sha256}'::VARCHAR AS manual_sha256,
            '{_sql_text(source_url)}'::VARCHAR AS source_url,
            r.source_row_number,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM raw_atlas_event r
        LEFT JOIN read_parquet('{_sql_path(dim_municipality_path)}') d
            ON r.Cod_IBGE_Mun = d.codigo_ibge
        ORDER BY r.source_row_number
        """
    )

    connection.execute(
        """
        CREATE TABLE fact_disaster_event AS
        SELECT
            source_event_id AS disaster_event_id,
            * EXCLUDE (source_row_number)
        FROM silver_disaster_event
        ORDER BY codigo_ibge, event_date, disaster_event_id
        """
    )

    dimension_path = _sql_path(dim_municipality_path)
    connection.execute(
        f"""
        CREATE TABLE snapshot_municipality_disaster_history AS
        WITH bounds AS (
            SELECT max(event_date)::DATE AS reference_date
            FROM fact_disaster_event
        )
        SELECT
            d.codigo_ibge,
            b.reference_date,
            min(f.event_date)::DATE AS first_event_date,
            max(f.event_date)::DATE AS latest_event_date,
            count(f.disaster_event_id)::BIGINT AS event_count,
            count(f.disaster_event_id) FILTER (WHERE f.is_rain_related)::BIGINT
                AS rain_related_event_count,
            count(f.disaster_event_id) FILTER (
                WHERE f.event_date > b.reference_date - INTERVAL 5 YEAR
            )::BIGINT AS event_count_5y,
            count(f.disaster_event_id) FILTER (
                WHERE f.event_date > b.reference_date - INTERVAL 10 YEAR
            )::BIGINT AS event_count_10y,
            count(f.disaster_event_id) FILTER (
                WHERE f.event_date > b.reference_date - INTERVAL 20 YEAR
            )::BIGINT AS event_count_20y,
            count(f.disaster_event_id) FILTER (
                WHERE f.is_rain_related
                  AND f.event_date > b.reference_date - INTERVAL 5 YEAR
            )::BIGINT AS rain_related_event_count_5y,
            count(f.disaster_event_id) FILTER (
                WHERE f.is_rain_related
                  AND f.event_date > b.reference_date - INTERVAL 10 YEAR
            )::BIGINT AS rain_related_event_count_10y,
            count(f.disaster_event_id) FILTER (
                WHERE f.is_rain_related
                  AND f.event_date > b.reference_date - INTERVAL 20 YEAR
            )::BIGINT AS rain_related_event_count_20y,
            coalesce(sum(f.deaths), 0)::HUGEINT AS deaths,
            coalesce(sum(f.injured), 0)::HUGEINT AS injured,
            coalesce(sum(f.homeless), 0)::HUGEINT AS homeless,
            coalesce(sum(f.displaced), 0)::HUGEINT AS displaced,
            coalesce(sum(f.direct_human_damage_total), 0)::HUGEINT
                AS direct_human_damage_total,
            coalesce(sum(f.reported_affected_total), 0)::HUGEINT
                AS reported_affected_total,
            '{_sql_text(source_release)}'::VARCHAR AS source_release,
            '{csv_sha256}'::VARCHAR AS source_sha256,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM read_parquet('{dimension_path}') d
        CROSS JOIN bounds b
        LEFT JOIN fact_disaster_event f USING (codigo_ibge)
        GROUP BY d.codigo_ibge, b.reference_date
        ORDER BY d.codigo_ibge
        """
    )

    connection.execute(
        """
        CREATE TABLE municipality_disaster_type_summary AS
        SELECT
            codigo_ibge,
            cobrade_code,
            min(event_date)::DATE AS first_event_date,
            max(event_date)::DATE AS latest_event_date,
            count(*)::BIGINT AS event_count,
            sum(deaths)::HUGEINT AS deaths,
            sum(injured)::HUGEINT AS injured,
            sum(homeless)::HUGEINT AS homeless,
            sum(displaced)::HUGEINT AS displaced,
            sum(direct_human_damage_total)::HUGEINT AS direct_human_damage_total,
            sum(reported_affected_total)::HUGEINT AS reported_affected_total,
            any_value(source_release)::VARCHAR AS source_release,
            any_value(source_sha256)::VARCHAR AS source_sha256,
            any_value(ingested_at)::TIMESTAMPTZ AS ingested_at
        FROM fact_disaster_event
        GROUP BY codigo_ibge, cobrade_code
        ORDER BY codigo_ibge, cobrade_code
        """
    )

    connection.execute(
        f"""
        CREATE TABLE municipality_disaster_month_profile AS
        SELECT
            d.codigo_ibge,
            months.month::TINYINT AS month,
            count(f.disaster_event_id)::BIGINT AS event_count,
            count(f.disaster_event_id) FILTER (WHERE f.is_rain_related)::BIGINT
                AS rain_related_event_count,
            '{_sql_text(source_release)}'::VARCHAR AS source_release,
            '{csv_sha256}'::VARCHAR AS source_sha256,
            TIMESTAMPTZ '{ingested_at.isoformat()}' AS ingested_at
        FROM read_parquet('{dimension_path}') d
        CROSS JOIN range(1, 13) months(month)
        LEFT JOIN fact_disaster_event f
            ON d.codigo_ibge = f.codigo_ibge
           AND months.month = f.event_month
        GROUP BY d.codigo_ibge, months.month
        ORDER BY d.codigo_ibge, months.month
        """
    )

    date_bounds = connection.execute(
        """
        SELECT
            min(event_date), max(event_date),
            min(registration_date), max(registration_date)
        FROM silver_disaster_event
        """
    ).fetchone()
    raw_bytes = csv_path.read_bytes()
    return SourceInspection(
        format="CSV",
        encoding="CP1252",
        delimiter=";",
        quote_character='"',
        line_ending="LF",
        columns=columns,
        column_count=len(columns),
        rows=connection.execute("SELECT count(*) FROM raw_atlas_event").fetchone()[0],
        physical_lines=raw_bytes.count(b"\n"),
        workbook_sheets=sheets,
        workbook_source_columns=workbook_descriptions["Atlas Valores Corrigidos"],
        correction_log_sheets=correction_log_sheets,
        first_event_date=date_bounds[0].isoformat(),
        latest_event_date=date_bounds[1].isoformat(),
        first_registration_date=date_bounds[2].isoformat(),
        latest_registration_date=date_bounds[3].isoformat(),
        municipality_count=connection.execute(
            "SELECT count(DISTINCT codigo_ibge) FROM silver_disaster_event"
        ).fetchone()[0],
        cobrade_count_observed=connection.execute(
            "SELECT count(DISTINCT cobrade_code) FROM silver_disaster_event"
        ).fetchone()[0],
        cobrade_count_dimension=connection.execute(
            "SELECT count(*) FROM dim_disaster_type"
        ).fetchone()[0],
        correction_reference_year=correction_reference_year,
        correction_reference_index=correction_reference_index,
    )


def _copy_atomically(
    connection: duckdb.DuckDBPyConnection, *, table: str, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection.execute(
        f"COPY {table} TO '{_sql_path(temporary)}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    temporary.replace(destination)


def write_atlas_artifacts(
    connection: duckdb.DuckDBPyConnection,
    *,
    silver_path: Path,
    correction_factor_path: Path,
    disaster_type_path: Path,
    fact_path: Path,
    snapshot_path: Path,
    type_summary_path: Path,
    month_profile_path: Path,
) -> None:
    for table, path in (
        ("silver_disaster_event", silver_path),
        ("atlas_monetary_correction_factor", correction_factor_path),
        ("dim_disaster_type", disaster_type_path),
        ("fact_disaster_event", fact_path),
        ("snapshot_municipality_disaster_history", snapshot_path),
        ("municipality_disaster_type_summary", type_summary_path),
        ("municipality_disaster_month_profile", month_profile_path),
    ):
        _copy_atomically(connection, table=table, destination=path)
