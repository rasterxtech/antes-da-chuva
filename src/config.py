from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
DOCS_DIR = PROJECT_ROOT / "docs"

SOURCE_NAME = "IBGE API de Localidades v1"
SOURCE_URL = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id"
)
SOURCE_DOCUMENTATION_URL = "https://servicodados.ibge.gov.br/api/docs/localidades"
DTB_REFERENCE_URL = (
    "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/"
    "estrutura-territorial/23701-divisao-territorial-brasileira.html"
)
DTB_2025_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/"
    "divisao_territorial/2025/DTB_2025.zip"
)
DTB_2025_RELEASE_URL = (
    "https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-"
    "noticias/noticias/46255-ibge-atualiza-dados-geograficos-de-estados-e-"
    "municipios-brasileiros-para-o-ano-de-2025"
)

RAW_JSON_PATH = RAW_DIR / "raw_ibge_municipalities.json"
RAW_METADATA_PATH = RAW_DIR / "raw_ibge_municipalities_metadata.json"
SILVER_PARQUET_PATH = SILVER_DIR / "silver_ibge_municipalities.parquet"
GOLD_PARQUET_PATH = GOLD_DIR / "dim_municipality.parquet"
GOLD_CSV_PATH = GOLD_DIR / "dim_municipality.csv"
QUALITY_JSON_PATH = GOLD_DIR / "data_quality_report.json"
QUALITY_MARKDOWN_PATH = DOCS_DIR / "data-quality-report.md"

REQUIRED_EXAMPLE_CODES = {
    "3304557": "Rio de Janeiro/RJ",
    "3550308": "Sao Paulo/SP",
    "4202404": "Blumenau/SC",
    "5300108": "Brasilia/DF",
}

SPECIAL_TERRITORIAL_TYPES = {
    "2605459": "distrito_estadual",
    "5300108": "distrito_federal",
}

MAPBIOMAS_COVERAGE_URL = (
    "https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-"
    "terra/cobertura-30m/cobertura/"
)
MAPBIOMAS_STATISTICS_DISCOVERY_URL = (
    "https://brasil.mapbiomas.org/downloads/estatisticas/"
)
MAPBIOMAS_LEGEND_DISCOVERY_URL = (
    "https://brasil.mapbiomas.org/downloads/codigos-de-legenda/"
)
MAPBIOMAS_URBANIZATION_URL = (
    "https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-"
    "terra/areas-urbanizadas/urbanizacao-anual/"
)
MAPBIOMAS_RAW_ROOT = RAW_DIR / "mapbiomas"
MAPBIOMAS_SILVER_PATH = SILVER_DIR / "mapbiomas_land_cover.parquet"
MAPBIOMAS_CLASS_LEGEND_PATH = SILVER_DIR / "mapbiomas_class_legend.parquet"
MAPBIOMAS_FACT_PATH = GOLD_DIR / "fact_municipality_land_cover.parquet"
MAPBIOMAS_SNAPSHOT_PATH = GOLD_DIR / "snapshot_municipality_land_cover.parquet"
MAPBIOMAS_CHANGE_PATH = GOLD_DIR / "municipality_land_cover_change.parquet"
MAPBIOMAS_QUALITY_JSON_PATH = GOLD_DIR / "mapbiomas_data_quality_report.json"
MAPBIOMAS_QUALITY_MARKDOWN_PATH = DOCS_DIR / "mapbiomas-data-quality-report.md"
MAPBIOMAS_DOC_PATH = DOCS_DIR / "mapbiomas.md"
MAPBIOMAS_RUNS_DIR = DATA_DIR / "manifests" / "mapbiomas"

ATLAS_DISCOVERY_URL = "https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml"
ATLAS_RAW_ROOT = RAW_DIR / "atlas"
ATLAS_SILVER_PATH = SILVER_DIR / "silver_disaster_event.parquet"
ATLAS_CORRECTION_FACTOR_PATH = SILVER_DIR / "atlas_monetary_correction_factor.parquet"
ATLAS_DISASTER_TYPE_PATH = SILVER_DIR / "dim_disaster_type.parquet"
ATLAS_FACT_PATH = GOLD_DIR / "fact_disaster_event.parquet"
ATLAS_SNAPSHOT_PATH = GOLD_DIR / "snapshot_municipality_disaster_history.parquet"
ATLAS_TYPE_SUMMARY_PATH = GOLD_DIR / "municipality_disaster_type_summary.parquet"
ATLAS_MONTH_PROFILE_PATH = GOLD_DIR / "municipality_disaster_month_profile.parquet"
ATLAS_QUALITY_JSON_PATH = GOLD_DIR / "atlas_data_quality_report.json"
ATLAS_QUALITY_MARKDOWN_PATH = DOCS_DIR / "atlas-data-quality-report.md"
ATLAS_DOC_PATH = DOCS_DIR / "atlas.md"
ATLAS_RUNS_DIR = DATA_DIR / "manifests" / "atlas"
