from datetime import datetime, timezone

import pytest

from src.transform.municipalities import normalize_name, transform_municipality


def raw_municipality() -> dict:
    return {
        "id": 3550308,
        "nome": "  São   Paulo  ",
        "microrregiao": {
            "id": 35061,
            "nome": "São Paulo",
            "mesorregiao": {"id": 3515, "nome": "Metropolitana de São Paulo"},
        },
        "regiao-imediata": {
            "id": 350001,
            "nome": "São Paulo",
            "regiao-intermediaria": {
                "id": 3501,
                "nome": "São Paulo",
                "UF": {
                    "id": 35,
                    "sigla": "SP",
                    "nome": "São Paulo",
                    "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                },
            },
        },
    }


def transform(raw: dict) -> dict:
    return transform_municipality(
        raw,
        source="IBGE",
        source_url="https://example.test",
        source_updated_at=None,
        ingested_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        special_territorial_types={"5300108": "distrito_federal"},
    )


def test_normalize_name_removes_accents_case_and_extra_spaces() -> None:
    assert normalize_name("  São   José do Rio Preto ") == "sao jose do rio preto"


def test_transform_uses_strings_for_administrative_codes() -> None:
    result = transform(raw_municipality())

    assert result["codigo_ibge"] == "3550308"
    assert result["codigo_uf_ibge"] == "35"
    assert result["codigo_regiao"] == "3"
    assert result["municipio"] == "  São   Paulo  "
    assert result["municipio_normalized"] == "sao paulo"
    assert result["tipo_unidade_territorial"] == "municipio"


def test_transform_accepts_missing_legacy_hierarchy() -> None:
    raw = raw_municipality()
    raw["microrregiao"] = None

    result = transform(raw)

    assert result["microrregiao"] is None
    assert result["mesorregiao"] is None
    assert result["regiao_imediata"] == "São Paulo"


def test_transform_rejects_missing_current_hierarchy() -> None:
    raw = raw_municipality()
    raw["regiao-imediata"] = None

    with pytest.raises(ValueError, match="regiao-imediata"):
        transform(raw)
