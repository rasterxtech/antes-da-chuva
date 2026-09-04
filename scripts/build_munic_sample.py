from __future__ import annotations

import json
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold" / "municipality_munic_capacity_2020.parquet"
MUNICIPAL_SAMPLE = ROOT / "data" / "samples" / "municipios.sample.json"
OUTPUT = ROOT / "data" / "samples" / "munic.sample.csv"


def run() -> None:
    if not GOLD.exists():
        raise RuntimeError("Execute python -m src.munic antes de gerar a amostra")
    municipalities = json.loads(MUNICIPAL_SAMPLE.read_text(encoding="utf-8"))
    codes = [str(record.get("code") or record.get("codigo_ibge")) for record in municipalities]
    if len(codes) != len(set(codes)):
        raise ValueError("A lista de municipios da amostra contem duplicatas")

    connection = duckdb.connect(":memory:")
    try:
        gold_path = str(GOLD).replace("'", "''")
        output_path = str(OUTPUT).replace("'", "''")
        placeholders = ", ".join("?" for _ in codes)
        count = connection.execute(
            f"SELECT count(*) FROM read_parquet('{gold_path}') WHERE codigo_ibge IN ({placeholders})",
            codes,
        ).fetchone()[0]
        if count != len(codes):
            raise ValueError(f"A GOLD retornou {count} de {len(codes)} municipios da amostra")
        connection.execute(
            f"""
            COPY (
                SELECT * EXCLUDE (ingested_at)
                FROM read_parquet('{gold_path}')
                WHERE codigo_ibge IN ({placeholders})
                ORDER BY codigo_ibge
            ) TO '{output_path}.tmp' (HEADER, DELIMITER ',')
            """,
            codes,
        )
    finally:
        connection.close()
    Path(f"{OUTPUT}.tmp").replace(OUTPUT)


if __name__ == "__main__":
    run()
    print(f"Amostra MUNIC gravada em {OUTPUT}")
