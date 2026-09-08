from pathlib import Path

import duckdb
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = PROJECT_ROOT / "data" / "gold" / "snapshot_municipality_land_cover.parquet"
CHANGE = PROJECT_ROOT / "data" / "gold" / "municipality_land_cover_change.parquet"


@pytest.mark.skipif(not SNAPSHOT.exists() or not CHANGE.exists(), reason="pipeline not run")
def test_materialized_mapbiomas_outputs_have_valid_grains_and_examples() -> None:
    connection = duckdb.connect(":memory:")
    snapshot_path = str(SNAPSHOT).replace("'", "''")
    change_path = str(CHANGE).replace("'", "''")
    snapshot_duplicates = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT codigo_ibge, year
            FROM read_parquet('{snapshot_path}')
            GROUP BY ALL HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    invalid_percentages = connection.execute(
        f"""
        SELECT count(*) FROM read_parquet('{snapshot_path}')
        WHERE urban_area_pct NOT BETWEEN 0 AND 100
           OR native_vegetation_area_pct NOT BETWEEN 0 AND 100
           OR agriculture_livestock_area_pct NOT BETWEEN 0 AND 100
           OR water_area_pct NOT BETWEEN 0 AND 100
           OR wetland_area_pct NOT BETWEEN 0 AND 100
        """
    ).fetchone()[0]
    examples = connection.execute(
        f"""
        SELECT count(DISTINCT codigo_ibge)
        FROM read_parquet('{snapshot_path}')
        WHERE codigo_ibge IN ('3550308', '3304557', '4202404', '5300108')
        """
    ).fetchone()[0]
    infinite_changes = connection.execute(
        f"""
        SELECT count(*) FROM read_parquet('{change_path}')
        WHERE isinf(urban_area_change_pct)
           OR isinf(urban_change_5y_pct)
           OR isinf(native_vegetation_change_pct)
        """
    ).fetchone()[0]
    connection.close()

    assert snapshot_duplicates == 0
    assert invalid_percentages == 0
    assert examples == 4
    assert infinite_changes == 0
