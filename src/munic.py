from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from src.config import (
    GOLD_PARQUET_PATH,
    MUNIC_GOLD_PATH,
    MUNIC_QUALITY_JSON_PATH,
    MUNIC_QUALITY_MARKDOWN_PATH,
    MUNIC_RAW_METADATA_PATH,
    MUNIC_RAW_PATH,
    MUNIC_REFERENCE_YEAR,
    MUNIC_RUNS_DIR,
    MUNIC_SILVER_PATH,
    MUNIC_SOURCE_NAME,
    MUNIC_SOURCE_PAGE_URL,
    MUNIC_SOURCE_URL,
    MUNIC_QUESTIONNAIRE_URL,
)
from src.extract.munic import extract_munic_workbook
from src.transform.munic import create_munic_tables, load_munic_records, write_munic_artifacts
from src.validation.munic import validate_munic, write_munic_quality_reports


def run() -> dict:
    if not GOLD_PARQUET_PATH.exists():
        raise RuntimeError("Execute python -m src.pipeline antes da carga MUNIC")

    ingested_at = datetime.now(timezone.utc).replace(microsecond=0)
    metadata = extract_munic_workbook(
        source_url=MUNIC_SOURCE_URL,
        source_name=MUNIC_SOURCE_NAME,
        raw_path=MUNIC_RAW_PATH,
        metadata_path=MUNIC_RAW_METADATA_PATH,
        ingested_at=ingested_at,
        reuse_existing=os.environ.get("MUNIC_FORCE_DOWNLOAD") != "1",
    )
    records = load_munic_records(
        MUNIC_RAW_PATH,
        source=MUNIC_SOURCE_NAME,
        source_url=MUNIC_SOURCE_URL,
        reference_year=MUNIC_REFERENCE_YEAR,
        ingested_at=ingested_at,
    )
    connection = create_munic_tables(records, dim_municipality_path=GOLD_PARQUET_PATH)
    try:
        report = validate_munic(
            connection,
            source_metadata={
                **metadata,
                "source_page_url": MUNIC_SOURCE_PAGE_URL,
                "questionnaire_url": MUNIC_QUESTIONNAIRE_URL,
            },
            generated_at=ingested_at.isoformat(),
        )
        write_munic_quality_reports(
            report,
            json_path=MUNIC_QUALITY_JSON_PATH,
            markdown_path=MUNIC_QUALITY_MARKDOWN_PATH,
        )
        if report["status"] != "PASS":
            raise RuntimeError(
                "A MUNIC falhou nas validacoes: " + ", ".join(report["problems_found"])
            )
        write_munic_artifacts(
            connection,
            silver_path=MUNIC_SILVER_PATH,
            gold_path=MUNIC_GOLD_PATH,
        )
    finally:
        connection.close()

    MUNIC_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = MUNIC_RUNS_DIR / "latest_successful_run.json"
    manifest.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    result = run()
    print(
        f"MUNIC 2020 criada: {result['rows']['silver']} registros de origem, "
        f"{result['rows']['gold']} unidades na GOLD."
    )
