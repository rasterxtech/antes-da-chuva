"""Validate the committed browser-facing presentation-data v1 files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "app" / "public" / "data" / "v1"
EXPECTED_MUNICIPALITY_COUNT = 5571
SCHEMA_VERSION = "v1"
CODE_PATTERN = re.compile(r"\d{7}\Z")
SHARD_PATTERN = re.compile(r"/data/v1/uf/([A-Z]{2})(?:-\d{3})?\.json\Z")
IDENTITY_FIELDS = (
    "codigo_ibge",
    "municipio",
    "municipio_normalized",
    "uf",
    "regiao",
    "regiao_imediata",
    "codigo_regiao_imediata",
    "tipo_unidade_territorial",
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.contracts.presentation import validate_presentation_payload


class ValidationError(Exception):
    """Raised when a generated frontend asset cannot be safely deployed."""


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"Required frontend asset is missing: {_relative(path)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"Invalid JSON in {_relative(path)}: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"Frontend asset must be a JSON object: {_relative(path)}")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string")
    return value


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def _validate_identity(value: object, label: str) -> tuple[str, dict[str, Any]]:
    identity = _require_object(value, label)
    for field in IDENTITY_FIELDS:
        _require_string(identity.get(field), f"{label}.{field}")
    code = identity["codigo_ibge"]
    if not CODE_PATTERN.fullmatch(code):
        raise ValidationError(f"{label}.codigo_ibge must be a seven-digit string")
    return code, identity


def _validate_metadata(metadata: dict[str, Any]) -> None:
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError("metadata.schema_version must be v1")

    universe = _require_object(metadata.get("territorial_universe"), "metadata.territorial_universe")
    if universe.get("id") != "ibge_current_5571":
        raise ValidationError("metadata.territorial_universe.id must be ibge_current_5571")
    if universe.get("municipality_count") != EXPECTED_MUNICIPALITY_COUNT:
        raise ValidationError(
            "metadata.territorial_universe.municipality_count must be 5571"
        )
    _require_string(universe.get("reference"), "metadata.territorial_universe.reference")

    sources = _require_object(metadata.get("sources"), "metadata.sources")
    source_fields = {
        "ibge": ("source", "query_date", "status"),
        "atlas": (
            "release",
            "first_year",
            "latest_year",
            "materialized_at",
            "source_sha256",
            "manifest",
        ),
        "mapbiomas": (
            "collection_id",
            "collection_version",
            "first_year",
            "latest_year",
            "materialized_at",
            "source_sha256",
            "manifest",
        ),
        "census": ("state", "reference"),
        "transferegov": ("state", "reference"),
    }
    for source, fields in source_fields.items():
        details = _require_object(sources.get(source), f"metadata.sources.{source}")
        for field in fields:
            value = details.get(field)
            if field.endswith("year"):
                if not isinstance(value, int) or isinstance(value, bool):
                    raise ValidationError(f"metadata.sources.{source}.{field} must be an integer")
            else:
                _require_string(value, f"metadata.sources.{source}.{field}")

    official_date = _require_object(sources["atlas"], "metadata.sources.atlas").get(
        "official_date"
    )
    if official_date is not None:
        _require_string(official_date, "metadata.sources.atlas.official_date")
    catalog = _require_object(sources["atlas"], "metadata.sources.atlas").get("catalog")
    if not isinstance(catalog, list) or len(catalog) != 5:
        raise ValidationError("metadata.sources.atlas.catalog must contain the five Atlas types")
    codes = []
    for item in catalog:
        item = _require_object(item, "metadata.sources.atlas.catalog item")
        if not isinstance(item.get("atlas_type_id"), int) or not isinstance(item.get("name"), str):
            raise ValidationError("Atlas catalog item is invalid")
        item_codes = item.get("cobrade_codes")
        if not isinstance(item_codes, list) or not all(isinstance(code, str) for code in item_codes):
            raise ValidationError("Atlas catalog COBRADE codes are invalid")
        codes.extend(item_codes)
    if len(codes) != 12 or len(set(codes)) != 12:
        raise ValidationError("metadata.sources.atlas.catalog must contain twelve unique COBRADE codes")


def _validate_index(index: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    if index.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError("municipal-index.schema_version must be v1")
    if index.get("territorial_universe") != "ibge_current_5571":
        raise ValidationError("municipal-index.territorial_universe must be ibge_current_5571")

    municipalities = index.get("municipalities")
    if not isinstance(municipalities, list):
        raise ValidationError("municipal-index.municipalities must be an array")
    if len(municipalities) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValidationError(
            f"municipal-index must contain {EXPECTED_MUNICIPALITY_COUNT} municipalities"
        )

    expected_by_shard: dict[str, dict[str, dict[str, Any]]] = {}
    codes: set[str] = set()
    for position, entry in enumerate(municipalities):
        code, identity = _validate_identity(entry, f"municipal-index.municipalities[{position}]")
        if code in codes:
            raise ValidationError(f"municipal-index has duplicate codigo_ibge: {code}")
        codes.add(code)

        shard = _require_string(identity.get("shard"), f"municipal-index[{code}].shard")
        shard_match = SHARD_PATTERN.fullmatch(shard)
        if shard_match is None:
            raise ValidationError(f"municipal-index[{code}].shard has an invalid path")
        if identity["uf"] != shard_match.group(1):
            raise ValidationError(f"municipal-index[{code}] UF does not match its shard")
        expected_by_shard.setdefault(shard, {})[code] = identity
    return expected_by_shard


def _validate_shard(
    shard: str,
    expected: dict[str, dict[str, Any]],
) -> set[str]:
    relative_shard = shard.removeprefix("/data/v1/")
    path = DATA_ROOT / relative_shard
    value = _load_json(path)

    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError(f"{_relative(path)}.schema_version must be v1")
    match = SHARD_PATTERN.fullmatch(shard)
    assert match is not None
    if value.get("uf") != match.group(1):
        raise ValidationError(f"{_relative(path)}.uf does not match its filename")

    municipalities = _require_object(value.get("municipalities"), f"{_relative(path)}.municipalities")
    actual_codes = set(municipalities)
    expected_codes = set(expected)
    if actual_codes != expected_codes:
        missing = sorted(expected_codes - actual_codes)
        unexpected = sorted(actual_codes - expected_codes)
        raise ValidationError(
            f"{_relative(path)} does not match municipal-index; "
            f"missing={missing[:3]} unexpected={unexpected[:3]}"
        )

    for code, payload in municipalities.items():
        if not isinstance(payload, dict):
            raise ValidationError(f"{_relative(path)}[{code}] must be an object")
        try:
            validate_presentation_payload(payload)
        except (TypeError, ValueError) as error:
            raise ValidationError(f"{_relative(path)}[{code}] violates the v1 schema: {error}") from error
        payload_code, identity = _validate_identity(
            payload.get("municipality"), f"{_relative(path)}[{code}].municipality"
        )
        if code != payload_code:
            raise ValidationError(f"{_relative(path)} key {code} disagrees with its payload")
        if identity != {field: expected[code][field] for field in IDENTITY_FIELDS}:
            raise ValidationError(f"{_relative(path)}[{code}] identity disagrees with municipal-index")
    return actual_codes


def _physical_shards(data_root: Path) -> set[str]:
    """Return every shard artifact physically present in the generated output."""
    shard_root = data_root / "uf"
    if not shard_root.is_dir():
        return set()
    return {
        f"/data/v1/{path.relative_to(data_root).as_posix()}"
        for path in shard_root.rglob("*")
        if path.is_file()
    }


def validate_frontend_data() -> None:
    """Validate v1 deployment assets without reading pipeline artifacts or DuckDB."""

    metadata_path = DATA_ROOT / "metadata.json"
    index_path = DATA_ROOT / "municipal-index.json"

    _validate_metadata(_load_json(metadata_path))
    expected_by_shard = _validate_index(_load_json(index_path))
    actual_by_shard = _physical_shards(DATA_ROOT)
    expected_shards = set(expected_by_shard)
    if actual_by_shard != expected_shards:
        orphaned = sorted(actual_by_shard - expected_shards)
        missing = sorted(expected_shards - actual_by_shard)
        raise ValidationError(
            f"UF shards do not match municipal-index; orphaned={orphaned[:3]} missing={missing[:3]}"
        )
    seen_codes: set[str] = set()
    for shard, expected in sorted(expected_by_shard.items()):
        shard_codes = _validate_shard(shard, expected)
        duplicate_codes = seen_codes & shard_codes
        if duplicate_codes:
            raise ValidationError(f"codigo_ibge duplicated across UF shards: {sorted(duplicate_codes)[:3]}")
        seen_codes.update(shard_codes)


def main() -> None:
    try:
        validate_frontend_data()
    except (OSError, ValidationError) as error:
        raise SystemExit(f"Frontend presentation-data validation failed: {error}") from error
    print("Frontend presentation-data v1 is complete and valid.")


if __name__ == "__main__":
    main()
