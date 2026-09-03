from __future__ import annotations

from datetime import datetime, timezone

from src.config import (
    GOLD_CSV_PATH,
    GOLD_PARQUET_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MARKDOWN_PATH,
    RAW_JSON_PATH,
    RAW_METADATA_PATH,
    SILVER_PARQUET_PATH,
    SOURCE_NAME,
    SOURCE_URL,
    SPECIAL_TERRITORIAL_TYPES,
)
from src.extract.ibge_municipalities import extract_ibge_municipalities
from src.transform.municipalities import (
    create_dimension_tables,
    transform_municipalities,
    write_dimension_artifacts,
)
from src.validation.municipalities import (
    validate_dimension,
    write_quality_reports,
)


def run() -> dict:
    ingested_at = datetime.now(timezone.utc).replace(microsecond=0)
    raw_records, source_metadata = extract_ibge_municipalities(
        source_url=SOURCE_URL,
        source_name=SOURCE_NAME,
        raw_path=RAW_JSON_PATH,
        metadata_path=RAW_METADATA_PATH,
        ingested_at=ingested_at,
    )
    silver_records = transform_municipalities(
        raw_records,
        source=SOURCE_NAME,
        source_url=SOURCE_URL,
        source_updated_at=source_metadata["source_updated_at"],
        ingested_at=ingested_at,
        special_territorial_types=SPECIAL_TERRITORIAL_TYPES,
    )
    connection = create_dimension_tables(silver_records)
    try:
        report = validate_dimension(
            connection,
            official_source_codes={str(record["id"]) for record in raw_records},
            generated_at=ingested_at,
            source_metadata=source_metadata,
        )
        write_quality_reports(
            report,
            json_path=QUALITY_JSON_PATH,
            markdown_path=QUALITY_MARKDOWN_PATH,
        )
        if report["status"] != "PASS":
            raise RuntimeError(
                "A dimensao falhou nas validacoes: "
                + ", ".join(report["problems_found"])
            )
        write_dimension_artifacts(
            connection,
            silver_path=SILVER_PARQUET_PATH,
            gold_parquet_path=GOLD_PARQUET_PATH,
            gold_csv_path=GOLD_CSV_PATH,
        )
    finally:
        connection.close()
    return report


if __name__ == "__main__":
    result = run()
    print(
        f"dim_municipality criada: {result['number_of_rows']} linhas, "
        f"{result['number_of_ufs']} UFs, {result['number_of_regions']} regioes."
    )
