from pathlib import Path

import duckdb
import pytest


ROOT = Path(__file__).resolve().parents[1]
FACT = ROOT / "data" / "gold" / "fact_disaster_event.parquet"
SILVER = ROOT / "data" / "silver" / "silver_disaster_event.parquet"
DISASTER_TYPE = ROOT / "data" / "silver" / "dim_disaster_type.parquet"
SNAPSHOT = ROOT / "data" / "gold" / "snapshot_municipality_disaster_history.parquet"
MONTH = ROOT / "data" / "gold" / "municipality_disaster_month_profile.parquet"
DIM = ROOT / "data" / "gold" / "dim_municipality.parquet"


@pytest.mark.skipif(
    not all(path.exists() for path in (FACT, SILVER, DISASTER_TYPE, SNAPSHOT, MONTH, DIM)),
    reason="pipeline Atlas not run",
)
def test_materialized_atlas_outputs_have_valid_grains_and_matching() -> None:
    connection = duckdb.connect(":memory:")
    paths = {
        name: str(path).replace("'", "''")
        for name, path in {
            "fact": FACT,
            "silver": SILVER,
            "disaster_type": DISASTER_TYPE,
            "snapshot": SNAPSHOT,
            "month": MONTH,
            "dim": DIM,
        }.items()
    }
    fact_duplicates = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT codigo_ibge, disaster_event_id
            FROM read_parquet('{paths['fact']}')
            GROUP BY ALL HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    snapshot_duplicates = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT codigo_ibge, reference_date
            FROM read_parquet('{paths['snapshot']}')
            GROUP BY ALL HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    fact_reconciliation = connection.execute(
        f"""
        SELECT
            (SELECT count(*) FROM read_parquet('{paths['fact']}')),
            (SELECT count(*) FROM read_parquet('{paths['silver']}')),
            (SELECT count(*) FROM read_parquet('{paths['fact']}')
             WHERE NOT is_dim_municipality_match),
            (SELECT count(*) FROM read_parquet('{paths['silver']}')
             WHERE NOT is_dim_municipality_match)
        """
    ).fetchone()
    counts = connection.execute(
        f"""
        SELECT
            (SELECT count(*) FROM read_parquet('{paths['snapshot']}')),
            (SELECT count(*) FROM read_parquet('{paths['dim']}')),
            (SELECT count(*) FROM read_parquet('{paths['month']}')),
            (SELECT sum(event_count) FROM read_parquet('{paths['snapshot']}')),
            (SELECT count(*) FROM read_parquet('{paths['fact']}'))
        """
    ).fetchone()
    connection.close()

    assert fact_duplicates == 0
    assert snapshot_duplicates == 0
    assert fact_reconciliation[0] == fact_reconciliation[1]
    assert fact_reconciliation[2] == fact_reconciliation[3]
    assert counts[0] == counts[1]
    assert counts[2] == counts[1] * 12
    assert counts[3] == counts[4] - fact_reconciliation[2]
