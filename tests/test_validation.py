from datetime import datetime, timezone

from src.transform.municipalities import create_dimension_tables
from src.validation.municipalities import validate_dimension


def record(code: str, name: str, uf_code: str, uf: str, acronym: str) -> dict:
    return {
        "codigo_ibge": code,
        "municipio": name,
        "municipio_normalized": name.lower(),
        "uf": uf,
        "sigla_uf": acronym,
        "codigo_uf_ibge": uf_code,
        "regiao": "Sudeste",
        "codigo_regiao": "3",
        "regiao_imediata": name,
        "codigo_regiao_imediata": uf_code + "0001",
        "regiao_intermediaria": name,
        "codigo_regiao_intermediaria": uf_code + "01",
        "mesorregiao": None,
        "codigo_mesorregiao": None,
        "microrregiao": None,
        "codigo_microrregiao": None,
        "tipo_unidade_territorial": "municipio",
        "source": "IBGE",
        "source_url": "https://example.test",
        "source_updated_at": None,
        "ingested_at": datetime(2026, 9, 1, tzinfo=timezone.utc),
    }


def metadata(count: int) -> dict:
    return {
        "source": "IBGE",
        "source_url": "https://example.test",
        "queried_at": "2026-09-01T00:00:00+00:00",
        "source_updated_at": None,
        "record_count": count,
    }


def test_validation_detects_duplicate_codes() -> None:
    records = [
        record("1100015", "Municipio A", "11", "Rondonia", "RO"),
        record("1100015", "Municipio B", "11", "Rondonia", "RO"),
    ]
    connection = create_dimension_tables(records)
    try:
        report = validate_dimension(
            connection,
            official_source_codes={"1100015"},
            generated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            source_metadata=metadata(1),
        )
    finally:
        connection.close()

    assert report["status"] == "FAIL"
    assert report["duplicate_codigo_ibge"] == 1
    assert "codigo_ibge_is_unique" in report["problems_found"]
