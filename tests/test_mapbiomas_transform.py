from pathlib import Path

import duckdb

from src.transform.mapbiomas import resolve_class_semantics


def test_class_semantics_are_resolved_from_official_names_and_hierarchy(
    tmp_path: Path,
) -> None:
    legend = tmp_path / "legend.csv"
    legend.write_text(
        "class_id,class_name_pt_br,class_name_en,hex_code\n"
        "3,Formação Florestal,Forest Formation,#000000\n"
        "11,Campo Alagado e Área Pantanosa,Wetland,#000000\n"
        "15,Pastagem,Pasture,#000000\n"
        "24,Área Urbanizada,Urban Area,#000000\n"
        "33,\"Rio, Lago e Oceano\",\"River, Lake and Ocean\",#000000\n",
        encoding="utf-8",
    )
    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE raw_mapbiomas_wide (
            "class" INTEGER,
            class_level_1 VARCHAR
        )
        """
    )
    connection.executemany(
        "INSERT INTO raw_mapbiomas_wide VALUES (?, ?)",
        [
            (0, "7. Not Observed"),
            (3, "1. Forest"),
            (11, "2. Herbaceous and Shrubby Vegetation"),
            (15, "3. Farming"),
            (24, "4. Non vegetated area"),
            (33, "5. Water"),
        ],
    )
    try:
        result = resolve_class_semantics(
            connection,
            legend_path=legend,
            urban_class_id_from_documentation=24,
        )
    finally:
        connection.close()

    assert result.urban_class_id == 24
    assert result.water_class_id == 33
    assert result.wetland_class_id == 11
    assert result.not_observed_class_ids == (0,)
    assert result.native_vegetation_class_ids == (3, 11)
    assert result.agriculture_livestock_class_ids == (15,)
    assert 0 not in result.mapped_class_ids
