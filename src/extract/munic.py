from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def extract_munic_workbook(
    *,
    source_url: str,
    source_name: str,
    raw_path: Path,
    metadata_path: Path,
    ingested_at: datetime,
    reuse_existing: bool = True,
    timeout_seconds: int = 120,
    max_attempts: int = 3,
) -> dict:
    """Baixa a planilha oficial da MUNIC ou reutiliza os mesmos bytes locais."""
    response_headers: dict[str, str | None] = {}
    http_status: int | None = None
    reused_local_file = reuse_existing and raw_path.exists()

    if reused_local_file:
        payload = raw_path.read_bytes()
    else:
        request = Request(
            source_url,
            headers={
                "Accept": "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet",
                "User-Agent": "antes-da-chuva-munic/1.0",
            },
        )
        for attempt in range(1, max_attempts + 1):
            try:
                with urlopen(request, timeout=timeout_seconds) as response:
                    payload = response.read()
                    http_status = response.status
                    headers = {
                        key.lower(): value for key, value in response.headers.items()
                    }
                response_headers = {
                    key: headers.get(key)
                    for key in (
                        "content-type",
                        "content-length",
                        "date",
                        "etag",
                        "last-modified",
                    )
                }
                break
            except (HTTPError, URLError, TimeoutError) as error:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"Falha ao baixar a MUNIC apos {max_attempts} tentativas"
                    ) from error
                time.sleep(2 ** (attempt - 1))
        _atomic_write(raw_path, payload)

    if not payload.startswith(b"PK"):
        raise ValueError("A fonte MUNIC recebida nao e um arquivo XLSX valido")

    metadata = {
        "source": source_name,
        "source_url": source_url,
        "reference_year": 2020,
        "ingested_at": ingested_at.isoformat(),
        "raw_file": _portable_path(raw_path),
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "http_status": http_status,
        "response_headers": response_headers,
        "reused_local_file": reused_local_file,
        "license": "unspecified",
        "license_note": (
            "Arquivo publico do IBGE; nenhuma licenca SPDX especifica foi "
            "identificada para esta edicao. Atribuir a MUNIC 2020."
        ),
    }
    _atomic_write(
        metadata_path,
        (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return metadata
