from src.contracts.atlas import required_fields, validate_fields
from src.transform.atlas import RAIN_RELATED_CODES


def test_atlas_schema_contract_requires_exact_fields_and_order() -> None:
    validate_fields(required_fields)
    changed = list(required_fields)
    changed[0], changed[1] = changed[1], changed[0]

    try:
        validate_fields(tuple(changed))
    except RuntimeError as error:
        assert "ordem_igual=False" in str(error)
    else:
        raise AssertionError("Uma mudanca de ordem deveria falhar")


def test_rain_classification_has_required_official_types() -> None:
    assert {"12100", "12200", "12300", "13214"} <= set(RAIN_RELATED_CODES)
    assert {"11311", "11321", "11331", "11340"} <= set(RAIN_RELATED_CODES)
