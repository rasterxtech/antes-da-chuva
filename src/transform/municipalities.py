from __future__ import annotations

import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb


SILVER_COLUMNS = (
    "codigo_ibge",
    "municipio",
    "municipio_normalized",
    "uf",
    "sigla_uf",
    "codigo_uf_ibge",
    "regiao",
    "codigo_regiao",
    "regiao_imediata",
    "codigo_regiao_imediata",
    "regiao_intermediaria",
    "codigo_regiao_intermediaria",
    "mesorregiao",
    "codigo_mesorregiao",
    "microrregiao",
    "codigo_microrregiao",
    "tipo_unidade_territorial",
    "source",
    "source_url",
    "source_updated_at",
    "ingested_at",
)


def normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(without_accents.casefold().split())


def _require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Hierarquia obrigatoria ausente ou invalida: {path}")
    return value


def transform_municipality(
    raw: dict[str, Any],
    *,
    source: str,
    source_url: str,
    source_updated_at: str | None,
    ingested_at: datetime,
    special_territorial_types: dict[str, str],
) -> dict[str, Any]:
    immediate = _require_mapping(raw.get("regiao-imediata"), "regiao-imediata")
    intermediate = _require_mapping(
        immediate.get("regiao-intermediaria"),
        "regiao-imediata.regiao-intermediaria",
    )
    uf = _require_mapping(
        intermediate.get("UF"), "regiao-imediata.regiao-intermediaria.UF"
    )
    region = _require_mapping(
        uf.get("regiao"), "regiao-imediata.regiao-intermediaria.UF.regiao"
    )

    code = str(raw["id"])
    municipality = str(raw["nome"])
    micro = raw.get("microrregiao")
    meso = micro.get("mesorregiao") if isinstance(micro, dict) else None

    return {
        "codigo_ibge": code,
        "municipio": municipality,
        "municipio_normalized": normalize_name(municipality),
        "uf": str(uf["nome"]),
        "sigla_uf": str(uf["sigla"]),
        "codigo_uf_ibge": str(uf["id"]),
        "regiao": str(region["nome"]),
        "codigo_regiao": str(region["id"]),
        "regiao_imediata": str(immediate["nome"]),
        "codigo_regiao_imediata": str(immediate["id"]),
        "regiao_intermediaria": str(intermediate["nome"]),
        "codigo_regiao_intermediaria": str(intermediate["id"]),
        "mesorregiao": str(meso["nome"]) if isinstance(meso, dict) else None,
        "codigo_mesorregiao": str(meso["id"]) if isinstance(meso, dict) else None,
        "microrregiao": str(micro["nome"]) if isinstance(micro, dict) else None,
        "codigo_microrregiao": str(micro["id"]) if isinstance(micro, dict) else None,
        "tipo_unidade_territorial": special_territorial_types.get(code, "municipio"),
        "source": source,
        "source_url": source_url,
        "source_updated_at": source_updated_at,
        "ingested_at": ingested_at,
    }


def transform_municipalities(
    records: list[dict[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return [transform_municipality(record, **kwargs) for record in records]


def create_dimension_tables(
    records: list[dict[str, Any]],
) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE silver_ibge_municipalities (
            codigo_ibge VARCHAR,
            municipio VARCHAR,
            municipio_normalized VARCHAR,
            uf VARCHAR,
            sigla_uf VARCHAR,
            codigo_uf_ibge VARCHAR,
            regiao VARCHAR,
            codigo_regiao VARCHAR,
            regiao_imediata VARCHAR,
            codigo_regiao_imediata VARCHAR,
            regiao_intermediaria VARCHAR,
            codigo_regiao_intermediaria VARCHAR,
            mesorregiao VARCHAR,
            codigo_mesorregiao VARCHAR,
            microrregiao VARCHAR,
            codigo_microrregiao VARCHAR,
            tipo_unidade_territorial VARCHAR,
            source VARCHAR,
            source_url VARCHAR,
            source_updated_at TIMESTAMPTZ,
            ingested_at TIMESTAMPTZ
        )
        """
    )
    placeholders = ", ".join("?" for _ in SILVER_COLUMNS)
    connection.executemany(
        f"INSERT INTO silver_ibge_municipalities VALUES ({placeholders})",
        [tuple(record[column] for column in SILVER_COLUMNS) for record in records],
    )
    connection.execute(
        """
        CREATE TABLE dim_municipality AS
        SELECT
            codigo_ibge,
            municipio,
            municipio_normalized,
            uf,
            sigla_uf,
            codigo_uf_ibge,
            regiao,
            codigo_regiao,
            regiao_imediata,
            codigo_regiao_imediata,
            regiao_intermediaria,
            codigo_regiao_intermediaria,
            tipo_unidade_territorial,
            source,
            source_url,
            source_updated_at,
            ingested_at
        FROM silver_ibge_municipalities
        ORDER BY sigla_uf, municipio
        """
    )
    return connection


def _copy_atomically(
    connection: duckdb.DuckDBPyConnection,
    *,
    query: str,
    destination: Path,
    copy_options: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()
    escaped_path = str(temporary_path).replace("'", "''")
    connection.execute(
        f"COPY ({query}) TO '{escaped_path}' ({copy_options})"
    )
    temporary_path.replace(destination)


def write_dimension_artifacts(
    connection: duckdb.DuckDBPyConnection,
    *,
    silver_path: Path,
    gold_parquet_path: Path,
    gold_csv_path: Path,
) -> None:
    _copy_atomically(
        connection,
        query="SELECT * FROM silver_ibge_municipalities ORDER BY sigla_uf, municipio",
        destination=silver_path,
        copy_options="FORMAT PARQUET, COMPRESSION ZSTD",
    )
    _copy_atomically(
        connection,
        query="SELECT * FROM dim_municipality",
        destination=gold_parquet_path,
        copy_options="FORMAT PARQUET, COMPRESSION ZSTD",
    )
    _copy_atomically(
        connection,
        query="SELECT * FROM dim_municipality",
        destination=gold_csv_path,
        copy_options="FORMAT CSV, HEADER TRUE",
    )
