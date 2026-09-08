from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


RESOURCE_ENV = {
    "csv": "ATLAS_CSV_URL",
    "xlsx": "ATLAS_XLSX_URL",
    "manual": "ATLAS_MANUAL_URL",
    "correction_log": "ATLAS_LOG_URL",
}


@dataclass(frozen=True)
class FetchedPage:
    url: str
    body: bytes
    content_type: str | None
    sha256: str


@dataclass(frozen=True)
class AtlasSource:
    source_release: str
    first_year: int
    latest_year: int
    version: str
    source_official_date: str
    discovery_url: str
    discovered_urls: dict[str, str]
    download_urls: dict[str, str]
    discovery_mode: str


@dataclass(frozen=True)
class AcquiredResource:
    resource_type: str
    artifact_path: Path
    manifest: dict[str, Any]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None
            self._text = []


def _request(url: str, headers: dict[str, str] | None = None) -> Request:
    return Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/octet-stream,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "antes-da-chuva-atlas/1.0",
            **(headers or {}),
        },
    )


def fetch_page(url: str, timeout_seconds: int = 90) -> FetchedPage:
    with urlopen(_request(url), timeout=timeout_seconds) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type")
    return FetchedPage(
        url=url,
        body=body,
        content_type=content_type,
        sha256=hashlib.sha256(body).hexdigest(),
    )


def _decode_page(page: FetchedPage) -> str:
    match = re.search(r"charset=([\w-]+)", page.content_type or "", re.I)
    return page.body.decode(match.group(1) if match else "utf-8")


def _single(values: list[str], description: str) -> str:
    unique = list(dict.fromkeys(values))
    if len(unique) != 1:
        raise RuntimeError(
            f"Descoberta Atlas sem confianca: esperava 1 {description}, "
            f"encontrei {len(unique)}"
        )
    return unique[0]


def _release_from_url(url: str) -> tuple[int, int, str, date]:
    filename = Path(unquote(urlparse(url).path)).name
    match = re.search(
        r"BD_Atlas_(\d{4})_(\d{4})_(v\d+(?:\.\d+)*)_"
        r"(\d{4})[._-](\d{2})[._-](\d{2})_Consolidado",
        filename,
        re.I,
    )
    if not match:
        raise RuntimeError(f"Release Atlas nao reconhecida no arquivo {filename!r}")
    first_year, latest_year, version, year, month, day = match.groups()
    return int(first_year), int(latest_year), version.lower(), date(
        int(year), int(month), int(day)
    )


def discover_atlas_source(page: FetchedPage) -> AtlasSource:
    parser = _LinkParser()
    parser.feed(_decode_page(page))
    links = [(urljoin(page.url, href), text.casefold()) for href, text in parser.links]

    csv_url = _single(
        [url for url, _ in links if urlparse(url).path.casefold().endswith(".csv")],
        "Base Completa CSV",
    )
    xlsx_url = _single(
        [
            url
            for url, text in links
            if urlparse(url).path.casefold().endswith(".xlsx")
            and "log" not in url.casefold()
            and "corre" not in url.casefold()
            and "log" not in text
        ],
        "Base Completa XLSX",
    )
    manual_url = _single(
        [url for url, _ in links if urlparse(url).path.casefold().endswith(".pdf")],
        "Manual de Tratamento PDF",
    )
    log_url = _single(
        [
            url
            for url, text in links
            if urlparse(url).path.casefold().endswith(".xlsx")
            and ("log" in url.casefold() or "corre" in url.casefold() or "log" in text)
        ],
        "Log de Correcoes XLSX",
    )

    csv_release = _release_from_url(csv_url)
    xlsx_release = _release_from_url(xlsx_url)
    if csv_release != xlsx_release:
        raise RuntimeError("As bases CSV e XLSX apontam para releases Atlas diferentes")
    first_year, latest_year, version, official_date = csv_release
    discovered_urls = {
        "csv": csv_url,
        "xlsx": xlsx_url,
        "manual": manual_url,
        "correction_log": log_url,
    }
    overrides = {
        name: os.environ[environment]
        for name, environment in RESOURCE_ENV.items()
        if os.environ.get(environment)
    }
    return AtlasSource(
        source_release=(
            f"atlas_{first_year}_{latest_year}_{version}_{official_date.isoformat()}"
        ),
        first_year=first_year,
        latest_year=latest_year,
        version=version,
        source_official_date=official_date.isoformat(),
        discovery_url=page.url,
        discovered_urls=discovered_urls,
        download_urls={**discovered_urls, **overrides},
        discovery_mode="override" if overrides else "automatic",
    )


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def preserve_discovery_page(page: FetchedPage, raw_root: Path) -> dict[str, Any]:
    path = raw_root / "discovery" / page.sha256[:12] / "downloads.html"
    if not path.exists():
        _atomic_write(path, page.body)
    return {
        "url": page.url,
        "sha256": page.sha256,
        "content_type": page.content_type,
        "path": str(path),
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_write(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def _response_filename(headers: Message, url: str) -> str:
    filename = headers.get_filename()
    if filename:
        return Path(filename).name
    filename = Path(unquote(urlparse(url).path)).name
    if not filename:
        raise RuntimeError(f"O recurso Atlas nao informou nome de arquivo: {url}")
    return filename


def acquire_resource(
    *,
    resource_type: str,
    source: AtlasSource,
    release_root: Path,
    checked_at: datetime,
    timeout_seconds: int = 240,
) -> AcquiredResource:
    manifest_path = release_root / "manifests" / f"{resource_type}.json"
    previous = _load_json(manifest_path)
    download_url = source.download_urls[resource_type]
    conditional_headers = {}
    same_download_url = bool(
        previous and previous.get("download_url") == download_url
    )
    if same_download_url and previous and previous.get("etag"):
        conditional_headers["If-None-Match"] = previous["etag"]
    if same_download_url and previous and previous.get("last_modified"):
        conditional_headers["If-Modified-Since"] = previous["last_modified"]

    temporary = release_root / "files" / f".{resource_type}.download.tmp"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        temporary.unlink()
    try:
        response = urlopen(
            _request(download_url, conditional_headers), timeout=timeout_seconds
        )
    except HTTPError as error:
        if error.code != 304 or not previous:
            raise
        artifact = Path(previous["artifact_path"])
        if not artifact.exists():
            raise RuntimeError("Fonte respondeu 304, mas o RAW anterior nao existe")
        manifest = {
            **previous,
            "discovery_url": source.discovery_url,
            "discovered_download_url": source.discovered_urls[resource_type],
            "download_url": download_url,
            "discovery_mode": source.discovery_mode,
            "last_checked_at": checked_at.isoformat(),
            "checks": previous.get("checks", [])
            + [{"checked_at": checked_at.isoformat(), "unchanged": True}],
        }
        _write_json(manifest_path, manifest)
        return AcquiredResource(resource_type, artifact, manifest)

    digest = hashlib.sha256()
    size = 0
    with response:
        headers = response.headers
        resolved_url = response.geturl()
        filename = _response_filename(headers, download_url)
        with temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        status = getattr(response, "status", None) or 200
    sha256 = digest.hexdigest()
    artifact = release_root / "files" / sha256[:12] / filename
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists():
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != sha256:
            raise RuntimeError(f"Colisao de hash no RAW Atlas: {artifact}")
        temporary.unlink()
    else:
        temporary.replace(artifact)

    checks = previous.get("checks", []) if previous else []
    checks.append(
        {
            "checked_at": checked_at.isoformat(),
            "sha256": sha256,
            "unchanged": bool(previous and previous.get("sha256") == sha256),
        }
    )
    manifest = {
        "source_name": "Atlas Digital de Desastres no Brasil / S2ID",
        "source_release": source.source_release,
        "resource_type": resource_type,
        "discovery_url": source.discovery_url,
        "discovered_download_url": source.discovered_urls[resource_type],
        "download_url": download_url,
        "resolved_download_url": resolved_url,
        "discovery_mode": source.discovery_mode,
        "original_filename": filename,
        "http_status": status,
        "http_headers": dict(headers.items()),
        "content_type": headers.get("Content-Type"),
        "content_length": size,
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "sha256": sha256,
        "source_official_date": source.source_official_date,
        "downloaded_at": (
            previous["downloaded_at"]
            if previous and previous.get("sha256") == sha256
            else checked_at.isoformat()
        ),
        "last_checked_at": checked_at.isoformat(),
        "artifact_path": str(artifact),
        "checks": checks,
    }
    _write_json(manifest_path, manifest)
    return AcquiredResource(resource_type, artifact, manifest)


def discover_and_acquire(
    *, discovery_url: str, raw_root: Path, checked_at: datetime
) -> tuple[AtlasSource, dict[str, AcquiredResource], dict[str, Any]]:
    page = fetch_page(discovery_url)
    source = discover_atlas_source(page)
    discovery_manifest = preserve_discovery_page(page, raw_root)
    release_root = raw_root / source.source_release
    resources = {
        resource_type: acquire_resource(
            resource_type=resource_type,
            source=source,
            release_root=release_root,
            checked_at=checked_at,
        )
        for resource_type in RESOURCE_ENV
    }
    return source, resources, discovery_manifest
