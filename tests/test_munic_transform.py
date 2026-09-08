from pathlib import Path

from openpyxl import Workbook

from src.contracts.munic import OUTPUT_STATUS_FIELDS, SOURCE_COLUMNS
from src.transform.munic import aggregate_status, load_munic_records, normalize_response


def test_response_states_are_not_collapsed() -> None:
    assert normalize_response("Sim") == "declared_yes"
    assert normalize_response("Não") == "declared_no"
    assert normalize_response("Recusa") == "refused"
    assert normalize_response("Não informou") == "not_reported"
    assert normalize_response("-") == "not_applicable"


def test_planning_aggregate_preserves_absence_and_unknown_states() -> None:
    assert aggregate_status(["declared_no", "declared_yes"]) == "declared_yes"
    assert aggregate_status(["declared_no", "declared_no"]) == "declared_no"
    assert aggregate_status(["refused", "refused"]) == "refused"


def test_workbook_mapping_and_compdec_unknown_override(tmp_path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Gestão de riscos"
    headers = list(dict.fromkeys(SOURCE_COLUMNS.values()))
    worksheet.append(headers)
    values = {header: "Não" for header in headers}
    values.update(
        {
            "CodMun": "4202404",
            "UF": "SC",
            "Mun": "Blumenau",
            "Mgrd171": "Sim",
            "Mgrd216": "Sim",
            "Mgrd225": "-",
            "Mgrd2213": "-",
        }
    )
    worksheet.append([values[header] for header in headers])
    path = tmp_path / "munic.xlsx"
    workbook.save(path)

    from datetime import datetime, timezone

    records = load_munic_records(
        path,
        source="fixture",
        source_url="https://example.test/munic.xlsx",
        reference_year=2020,
        ingested_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    assert len(records) == 1
    assert set(OUTPUT_STATUS_FIELDS).issubset(records[0])
    assert records[0]["municipal_civil_defense_body_status"] == "unknown"
    assert records[0]["any_risk_prevention_planning_instrument_status"] == "declared_yes"
    assert records[0]["civil_defense_budget_provision_status"] == "not_applicable"
