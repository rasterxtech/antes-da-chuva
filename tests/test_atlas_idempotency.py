from pathlib import Path

from src.atlas import _file_sha256, is_unchanged


def test_atlas_idempotency_requires_same_inputs_pipeline_and_outputs(
    tmp_path: Path,
) -> None:
    output = tmp_path / "fact.parquet"
    output.write_bytes(b"present")
    signature = {"source_release": "release", "source_hashes": {"csv": "abc"}}
    previous = {
        "input_signature": signature,
        "pipeline_fingerprint": "pipeline",
        "output_hashes": {str(output): _file_sha256(output)},
    }

    assert is_unchanged(
        previous,
        signature=signature,
        pipeline_fingerprint="pipeline",
        output_paths=(output,),
    )
    assert not is_unchanged(
        previous,
        signature={**signature, "source_release": "new"},
        pipeline_fingerprint="pipeline",
        output_paths=(output,),
    )
    assert not is_unchanged(
        previous,
        signature=signature,
        pipeline_fingerprint="changed",
        output_paths=(output,),
    )

    output.write_bytes(b"corrupted")
    assert not is_unchanged(
        previous,
        signature=signature,
        pipeline_fingerprint="pipeline",
        output_paths=(output,),
    )
