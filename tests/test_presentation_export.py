from __future__ import annotations

import copy
import json
from pathlib import Path

import duckdb
import pytest

from scripts.export_frontend_data import _partition_uf_payloads, export_frontend_data
from src.contracts.presentation import PRESENTATION_STATES, validate_presentation_payload


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "presentation_v1"

TABLES = {
    "dim_municipality": (
        "codigo_ibge VARCHAR, municipio VARCHAR, municipio_normalized VARCHAR, "
        "sigla_uf VARCHAR, regiao VARCHAR, regiao_imediata VARCHAR, "
        "tipo_unidade_territorial VARCHAR, codigo_regiao_imediata VARCHAR DEFAULT 'fixture-region'",
        "dim_municipality.parquet",
    ),
    "snapshot_municipality_disaster_history": (
        "codigo_ibge VARCHAR, first_event_date VARCHAR, latest_event_date VARCHAR, "
        "event_count BIGINT, rain_related_event_count BIGINT, deaths DOUBLE, "
        "injured DOUBLE, homeless DOUBLE, displaced DOUBLE, missing DOUBLE, "
        "reference_date VARCHAR, rain_related_event_count_10y BIGINT",
        "snapshot_municipality_disaster_history.parquet",
    ),
    "municipality_disaster_type_summary": (
        "codigo_ibge VARCHAR, cobrade_code VARCHAR, type_name VARCHAR, "
        "first_event_date VARCHAR, latest_event_date VARCHAR, event_count BIGINT, "
        "deaths DOUBLE, injured DOUBLE, homeless DOUBLE, displaced DOUBLE, "
        "reported_affected_total DOUBLE",
        "municipality_disaster_type_summary.parquet",
    ),
    "municipality_disaster_month_profile": (
        "codigo_ibge VARCHAR, month TINYINT, event_count BIGINT, "
        "rain_related_event_count BIGINT",
        "municipality_disaster_month_profile.parquet",
    ),
    "fact_disaster_event": (
        "codigo_ibge VARCHAR, cobrade_code VARCHAR, atlas_type_name_source VARCHAR, "
        "is_federally_recognized BOOLEAN, is_rain_related BOOLEAN, missing BIGINT, "
        "atlas_type_id SMALLINT DEFAULT 1, event_year SMALLINT DEFAULT 2025, "
        "event_date DATE DEFAULT '2025-12-31'",
        "fact_disaster_event.parquet",
    ),
    "snapshot_municipality_land_cover": (
        "codigo_ibge VARCHAR, year INTEGER, mapped_area_ha DOUBLE, urban_area_ha DOUBLE, "
        "urban_area_pct DOUBLE, native_vegetation_area_ha DOUBLE, "
        "native_vegetation_area_pct DOUBLE, water_area_ha DOUBLE, wetland_area_ha DOUBLE, "
        "agriculture_livestock_area_ha DOUBLE DEFAULT 0, agriculture_livestock_area_pct DOUBLE DEFAULT 0, "
        "water_area_pct DOUBLE DEFAULT 0, wetland_area_pct DOUBLE DEFAULT 0",
        "snapshot_municipality_land_cover.parquet",
    ),
    "municipality_land_cover_change": (
        "codigo_ibge VARCHAR, first_year INTEGER, latest_year INTEGER, "
        "reference_year_5y INTEGER, reference_year_10y INTEGER, reference_year_20y INTEGER, "
        "urban_area_first_year_ha DOUBLE, urban_area_latest_year_ha DOUBLE, "
        "urban_area_change_ha DOUBLE, urban_area_change_pct DOUBLE, urban_change_5y_ha DOUBLE, "
        "urban_change_5y_pct DOUBLE, urban_change_10y_ha DOUBLE, urban_change_10y_pct DOUBLE, "
        "urban_change_20y_ha DOUBLE, urban_change_20y_pct DOUBLE, "
        "native_vegetation_first_year_ha DOUBLE, native_vegetation_latest_year_ha DOUBLE, "
        "native_vegetation_change_ha DOUBLE, native_vegetation_change_pct DOUBLE, "
        "native_vegetation_change_5y_ha DOUBLE, native_vegetation_change_5y_pct DOUBLE, "
        "native_vegetation_change_10y_ha DOUBLE, native_vegetation_change_10y_pct DOUBLE, "
        "native_vegetation_change_20y_ha DOUBLE, native_vegetation_change_20y_pct DOUBLE, "
        "water_area_change_10y_ha DOUBLE, wetland_area_change_10y_ha DOUBLE",
        "municipality_land_cover_change.parquet",
    ),
    "municipality_munic_capacity_2020": (
        "codigo_ibge VARCHAR, in_source BOOLEAN, "
        "municipal_civil_defense_body_status VARCHAR, "
        "civil_defense_budget_provision_status VARCHAR, "
        "any_risk_prevention_planning_instrument_status VARCHAR, "
        "flood_risk_mapping_status VARCHAR, flood_contingency_plan_status VARCHAR, "
        "flood_early_warning_status VARCHAR, landslide_risk_mapping_status VARCHAR, "
        "landslide_contingency_plan_status VARCHAR, landslide_early_warning_status VARCHAR, "
        "source_year INTEGER",
        "municipality_munic_capacity_2020.parquet",
    ),
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _materialize_fixture(root: Path, fixture: dict | None = None) -> Path:
    if fixture is None:
        fixture = json.loads((FIXTURES / "gold_fixture.json").read_text(encoding="utf-8"))
    if "municipality_munic_capacity_2020" not in fixture:
        munic_rows = []
        for municipality in fixture["dim_municipality"]:
            code = municipality[0]
            if code == "5101837":
                munic_rows.append([code, False, *(["not_in_source"] * 9), 2020])
            elif code == "4202404":
                munic_rows.append([
                    code, True, "declared_yes", "declared_yes", "declared_yes",
                    "declared_yes", "declared_no", "not_reported", "declared_yes",
                    "declared_no", "unknown", 2020,
                ])
            else:
                munic_rows.append([code, True, *(["declared_no"] * 9), 2020])
        fixture["municipality_munic_capacity_2020"] = munic_rows
    gold_dir = root / "data" / "gold"
    gold_dir.mkdir(parents=True)
    connection = duckdb.connect(":memory:")
    try:
        for table, (schema, filename) in TABLES.items():
            rows = fixture[table]
            connection.execute(f"CREATE TABLE {table} ({schema})")
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info('{table}')").fetchall()]
            source_columns = ", ".join(columns[: len(rows[0])])
            placeholders = ", ".join("?" for _ in rows[0])
            connection.executemany(
                f"INSERT INTO {table} ({source_columns}) VALUES ({placeholders})", rows
            )
            output = str(gold_dir / filename).replace("'", "''")
            connection.execute(f"COPY {table} TO '{output}' (FORMAT PARQUET)")
    finally:
        connection.close()

    _write_json(
        gold_dir / "data_quality_report.json",
        {
            "number_of_rows": len(fixture["dim_municipality"]),
            "source": "IBGE API de Localidades v1",
            "source_query_date": "2026-09-02",
            "status": "PASS",
        },
    )
    _write_json(
        gold_dir / "atlas_data_quality_report.json",
        {
            "source_inspection": {
                "first_event_date": "1991-01-07",
                "latest_event_date": "2025-12-31",
            }
        },
    )
    _write_json(
        root / "data" / "manifests" / "atlas" / "latest_successful_run.json",
        {
            "source_release": "atlas_fixture",
            "finished_at": "2026-09-02T21:06:38+00:00",
            "input_signature": {"source_official_date": "2026-08-06"},
            "source_hashes": {"csv": "fixture-atlas"},
        },
    )
    _write_json(
        root / "data" / "manifests" / "mapbiomas" / "latest_successful_run.json",
        {
            "collection_id": "11",
            "collection_version": "v1",
            "first_year": 1985,
            "latest_year": 2025,
            "finished_at": "2026-09-02T21:05:56+00:00",
            "source_hashes": {"statistics": "fixture-mapbiomas"},
        },
    )
    _write_json(
        root / "data" / "manifests" / "munic" / "latest_successful_run.json",
        {
            "status": "PASS",
            "generated_at": "2026-09-03T22:00:00+00:00",
            "source": {
                "reference_year": 2020,
                "sha256": "fixture-munic",
            },
        },
    )
    legacy = root / "app" / "public" / "data" / "municipios.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        (FIXTURES / "legacy_municipalities.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return legacy


def _payload(output_dir: Path, code: str) -> dict:
    index = json.loads((output_dir / "municipal-index.json").read_text(encoding="utf-8"))
    entry = next(item for item in index["municipalities"] if item["codigo_ibge"] == code)
    shard = output_dir / entry["shard"].removeprefix("/data/v1/")
    return json.loads(shard.read_text(encoding="utf-8"))["municipalities"][code]


@pytest.fixture()
def exported_fixture(tmp_path: Path) -> tuple[Path, dict]:
    legacy = _materialize_fixture(tmp_path)
    output = tmp_path / "output"
    result = export_frontend_data(
        project_root=tmp_path,
        output_dir=output,
        legacy_municipalities_path=legacy,
        verify_manifest_hashes=False,
    )
    return output, result


def test_contract_keeps_codigo_ibge_as_text_and_matches_typescript(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    payload = _payload(output, "4202404")
    validate_presentation_payload(payload)
    assert payload["municipality"]["codigo_ibge"] == "4202404"
    assert isinstance(payload["municipality"]["codigo_ibge"], str)
    assert payload["municipality"]["regiao_imediata"] == "Blumenau"
    assert payload["municipal_capacity"]["state"] == "record"
    assert payload["municipal_capacity"]["indicators"]["municipal_civil_defense_body"] == "declared_yes"
    assert payload["summary"]["thirty_second_text"] == (
        "Desde 1991, foram encontrados 32 registros relacionados à chuva em Blumenau. "
        "Enxurradas é o tipo mais frequente na série consultada. O registro mais recente "
        "é de 2025. No território, a área classificada como urbanizada passou de 0.01 "
        "km² em 1985 para 1.57 km² em 2025."
    )

    invalid = copy.deepcopy(payload)
    invalid["municipality"]["codigo_ibge"] = 4202404
    with pytest.raises(ValueError, match="codigo_ibge"):
        validate_presentation_payload(invalid)

    typescript_contract = (ROOT / "app" / "lib" / "presentation-contract.ts").read_text(
        encoding="utf-8"
    )
    for state in PRESENTATION_STATES:
        assert f"'{state}'" in typescript_contract


def test_export_is_deterministic(tmp_path: Path) -> None:
    legacy = _materialize_fixture(tmp_path)
    first = export_frontend_data(
        project_root=tmp_path,
        output_dir=tmp_path / "first",
        legacy_municipalities_path=legacy,
        verify_manifest_hashes=False,
    )
    second = export_frontend_data(
        project_root=tmp_path,
        output_dir=tmp_path / "second",
        legacy_municipalities_path=legacy,
        verify_manifest_hashes=False,
    )
    assert first["sha256"] == second["sha256"]


def test_export_partitions_uf_at_reduced_limit_in_codigo_ibge_order() -> None:
    municipalities = {
        "4202404": {"value": "b" * 100},
        "4202305": {"value": "a" * 100},
    }
    individual_limit = len(
        json.dumps(
            {"schema_version": "v1", "uf": "SC", "municipalities": {"4202305": municipalities["4202305"]}},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ) + 1
    partitions = _partition_uf_payloads("SC", municipalities, individual_limit)
    assert [list(partition) for partition in partitions] == [["4202305"], ["4202404"]]


def test_export_aborts_when_one_municipality_exceeds_reduced_limit(tmp_path: Path) -> None:
    legacy = _materialize_fixture(tmp_path)
    with pytest.raises(ValueError, match="Payload municipal"):
        export_frontend_data(
            project_root=tmp_path,
            output_dir=tmp_path / "too-small",
            legacy_municipalities_path=legacy,
            verify_manifest_hashes=False,
            max_shard_bytes=1,
        )


def test_30_second_template_distinguishes_atlas_and_mapbiomas_absences(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    no_atlas = _payload(output, "1200013")
    assert no_atlas["summary"]["thirty_second_text"] == (
        "Nenhum registro foi encontrado nesta release do Atlas/S2ID."
    )
    assert "Nunca houve desastre" not in no_atlas["summary"]["thirty_second_text"]

    no_mapbiomas = _payload(output, "2605459")
    assert no_mapbiomas["land_cover"]["state"] == "no_coverage"
    assert "área classificada como urbanizada" not in no_mapbiomas["summary"][
        "thirty_second_text"
    ]


def test_municipal_index_is_unique_and_has_no_parquet(exported_fixture: tuple[Path, dict]) -> None:
    output, result = exported_fixture
    index = json.loads((output / "municipal-index.json").read_text(encoding="utf-8"))
    codes = [item["codigo_ibge"] for item in index["municipalities"]]
    assert len(codes) == result["municipalities"] == len(set(codes))
    assert all(isinstance(code, str) and len(code) == 7 for code in codes)
    assert not list(output.rglob("*.parquet"))


def test_all_mandatory_edge_municipalities_keep_expected_states(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    expectations = json.loads(
        (FIXTURES / "expected_edge_states.json").read_text(encoding="utf-8")
    )
    for code, expected in expectations.items():
        payload = _payload(output, code)
        assert payload["disasters"]["state"] == expected["disasters"]
        assert payload["land_cover"]["state"] == expected["land_cover"]
        assert payload["census"]["state"] == expected["census"]
        assert payload["transfers"]["state"] == expected["transfers"]
        assert (
            payload["municipality"]["tipo_unidade_territorial"]
            == expected["territorial_type"]
        )

    blumenau = _payload(output, "4202404")
    assert blumenau["land_cover"]["history"][0]["wetland_area_ha"] == 0
    assert blumenau["land_cover"]["state"] == "record"
    acrelandia = _payload(output, "1200013")
    assert acrelandia["disasters"]["state"] == "no_record"
    assert acrelandia["disasters"]["history"]["all_event_count"] == 7
    assert acrelandia["summary"]["thirty_second_text"] == (
        "Nenhum registro foi encontrado nesta release do Atlas/S2ID."
    )
    fernando_de_noronha = _payload(output, "2605459")
    assert fernando_de_noronha["land_cover"]["state"] == "no_coverage"
    assert fernando_de_noronha["land_cover"]["history"] == []
    boa_esperanca = _payload(output, "5101837")
    assert boa_esperanca["municipal_capacity"]["state"] == "not_in_source"
    assert set(boa_esperanca["municipal_capacity"]["indicators"].values()) == {"not_in_source"}


def test_annual_benchmark_months_and_type_percentages_are_reconciled(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    payload = _payload(output, "4202404")
    annual = payload["disasters"]["history"]["annual"]
    assert annual["benchmark"]["immediate_region"]["zeros_policy"] == "included_as_zero"
    assert annual["benchmark"]["immediate_region"]["municipality_count"] == 9
    total_series = next(series for series in annual["series"] if series["atlas_type_id"] is None)
    assert [point["year"] for point in total_series["points"]] == list(range(2004, 2026))
    assert total_series["points"][-1]["municipal_event_count"] == 1
    assert total_series["points"][-1]["immediate_region_average_event_count"] == pytest.approx(1 / 9)
    assert len(payload["disasters"]["months"]) == 12
    assert payload["disasters"]["months"][0]["event_pct"] == pytest.approx(6 / 32 * 100)
    assert sum(item["event_pct"] for item in payload["disasters"]["types"]) == pytest.approx(100)
    assert [item["atlas_type_id"] for item in payload["disasters"]["types"]].count(8) == 1
    mass = next(item for item in payload["disasters"]["types"] if item["atlas_type_id"] == 8)
    assert mass["event_count"] == mass["deaths"] == 2
    assert mass["cobrade_codes"] == ["11311", "11312", "11313", "11314", "11321", "11331", "11332", "11340"]
    no_record = _payload(output, "1200013")
    assert all(month["event_pct"] is None for month in no_record["disasters"]["months"])


def test_immediate_region_benchmarks_have_five_metrics_and_reconciled_denominators(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    benchmark = _payload(output, "4202404")["benchmarks"]["immediate_region"]
    assert benchmark["includes_selected_municipality"] is True
    assert set(benchmark["metrics"]) == {
        "rain_related_event_count_10y", "urban_change_20y_pct",
        "native_vegetation_change_20y_pct", "urban_area_pct", "native_vegetation_area_pct",
    }
    rain = benchmark["metrics"]["rain_related_event_count_10y"]
    assert rain["reference"]["reference_date"] == "2025-12-31"
    assert rain["municipality_value"] == 3
    assert rain["denominator"] == {"included": 9, "missing": 0, "undefined": 0}
    for metric in benchmark["metrics"].values():
        assert sum(metric["denominator"].values()) == benchmark["municipality_count"]


def test_rain_benchmark_uses_snapshot_reference_and_strict_ten_year_boundary(
    tmp_path: Path,
) -> None:
    # Given: a canonical snapshot ending on a non-rain event, with a leap-day event
    # strictly after its ten-year boundary.
    fixture = json.loads((FIXTURES / "gold_fixture.json").read_text(encoding="utf-8"))
    fixture["fact_disaster_event"] = [
        ["4202404", "12200", "Enxurrada", True, True, 0, 2, 2016, "2016-02-28"],
        ["4202404", "12200", "Enxurrada", True, True, 0, 2, 2016, "2016-02-29"],
        ["4202404", "99999", "Outro", True, False, 0, 2, 2026, "2026-02-28"],
    ]
    fixture["municipality_disaster_type_summary"] = [
        ["4202404", "12200", "Enxurrada", "2016-02-28", "2016-02-29", 2, 0, 0, 0, 0, 0]
    ]
    snapshot = next(
        row
        for row in fixture["snapshot_municipality_disaster_history"]
        if row[0] == "4202404"
    )
    snapshot[-2:] = ["2026-02-28", 1]
    snapshot[1:5] = ["2016-02-28", "2026-02-28", 3, 2]
    for row in fixture["snapshot_municipality_disaster_history"]:
        if row is not snapshot:
            row[4] = 0
            row[-2:] = ["2026-02-28", 0]
    snapshot[4] = 2

    # When: the presentation export is generated from the canonical GOLDs.
    legacy = _materialize_fixture(tmp_path, fixture)
    output = tmp_path / "output"
    export_frontend_data(
        project_root=tmp_path,
        output_dir=output,
        legacy_municipalities_path=legacy,
        verify_manifest_hashes=False,
    )

    # Then: the regional metric preserves the snapshot's date and strict boundary count.
    rain = _payload(output, "4202404")["benchmarks"]["immediate_region"]["metrics"][
        "rain_related_event_count_10y"
    ]
    assert rain["reference"]["reference_date"] == "2026-02-28"
    assert rain["municipality_value"] == 1


def test_land_cover_payload_reconciles_snapshots_and_changes_with_gold(
    exported_fixture: tuple[Path, dict],
) -> None:
    output, _ = exported_fixture
    payload = _payload(output, "4202404")["land_cover"]
    gold_dir = output.parent / "data" / "gold"
    connection = duckdb.connect(":memory:")
    try:
        snapshot_cursor = connection.execute(
            """
            SELECT year, mapped_area_ha, urban_area_ha, urban_area_pct,
                   native_vegetation_area_ha, native_vegetation_area_pct,
                   agriculture_livestock_area_ha, agriculture_livestock_area_pct,
                   water_area_ha, water_area_pct, wetland_area_ha, wetland_area_pct
            FROM read_parquet(?)
            WHERE codigo_ibge = ?
            ORDER BY year
            """,
            [str(gold_dir / "snapshot_municipality_land_cover.parquet"), "4202404"],
        )
        snapshot_columns = [column[0] for column in snapshot_cursor.description]
        snapshot_rows = snapshot_cursor.fetchall()
        change_row = connection.execute(
            """
            SELECT urban_area_change_ha, urban_area_change_pct,
                   native_vegetation_change_ha, native_vegetation_change_pct
            FROM read_parquet(?)
            WHERE codigo_ibge = ?
            """,
            [str(gold_dir / "municipality_land_cover_change.parquet"), "4202404"],
        ).fetchone()
    finally:
        connection.close()

    assert [snapshot[0] for snapshot in snapshot_rows] == [1985, 2025]
    assert payload["history"] == [
        {"codigo_ibge": "4202404", **dict(zip(snapshot_columns, row, strict=True))}
        for row in snapshot_rows
    ]
    assert {
        field: payload["change"][field]
        for field in (
            "urban_area_change_ha",
            "urban_area_change_pct",
            "native_vegetation_change_ha",
            "native_vegetation_change_pct",
        )
    } == {
        "urban_area_change_ha": change_row[0],
        "urban_area_change_pct": change_row[1],
        "native_vegetation_change_ha": change_row[2],
        "native_vegetation_change_pct": change_row[3],
    }
