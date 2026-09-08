from pathlib import Path

from scripts.validate_frontend_data import _physical_shards


def test_physical_shards_include_untracked_artifacts_and_orphans(tmp_path: Path) -> None:
    shard_root = tmp_path / "uf"
    shard_root.mkdir()
    (shard_root / "MG-001.json").write_text("{}", encoding="utf-8")
    (shard_root / "orphan.json").write_text("{}", encoding="utf-8")

    assert _physical_shards(tmp_path) == {
        "/data/v1/uf/MG-001.json",
        "/data/v1/uf/orphan.json",
    }
