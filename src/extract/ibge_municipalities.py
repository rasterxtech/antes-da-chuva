from __future__ import annotations

import gzip
import hashlib
import json
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def _parse_http_datetime(value: str | None) -> str | None:
    if not value:
        return None
    parsed = parsedate_to_datetime(value)
    return parsed.isoformat()


def extract_ibge_municipalities(
    *,
    source_url: str,
    source_name: str,
    raw_path: Path,
    metadata_path: Path,
    ingested_at: datetime,
    timeout_seconds: int = 90,
    max_attempts: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Baixa e preserva sem alteracao a resposta da API de Localidades."""
    request = Request(
        source_url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "antes-da-chuva-dim-municipality/1.0",
        },
    )

    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read()
                status = response.status
                headers = {key.lower(): value for key, value in response.headers.items()}
            break
        except (HTTPError, URLError, TimeoutError) as error:
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Falha ao consultar o IBGE apos {max_attempts} tentativas"
                ) from error
            time.sleep(2 ** (attempt - 1))

    transport_payload = payload
    content_encoding = headers.get("content-encoding")
    if content_encoding == "gzip" or payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)

    try:
        records = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("A resposta do IBGE nao e um JSON valido") from error

    if not isinstance(records, list) or not records:
        raise ValueError("A resposta do IBGE deve ser uma lista nao vazia")

    _atomic_write(raw_path, payload)

    source_updated_at = _parse_http_datetime(headers.get("last-modified"))
    metadata = {
        "source": source_name,
        "source_url": source_url,
        "queried_at": ingested_at.isoformat(),
        "source_updated_at": source_updated_at,
        "http_status": status,
        "record_count": len(records),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "transport_sha256": hashlib.sha256(transport_payload).hexdigest(),
        "transport_content_encoding": content_encoding,
        "raw_file": str(raw_path),
        "response_headers": {
            key: headers.get(key)
            for key in (
                "content-type",
                "date",
                "etag",
                "last-modified",
                "cache-control",
                "content-encoding",
            )
        },
        "original_top_level_fields": sorted(
            {field for record in records for field in record.keys()}
        ),
    }
    _atomic_write(
        metadata_path,
        (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return records, metadata
