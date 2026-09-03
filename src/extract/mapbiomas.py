from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


MONTHS_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _ascii_lower(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    ).casefold()


def _attributes(values: list[tuple[str, str | None]]) -> dict[str, str]:
    return {key: value or "" for key, value in values}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.links: list[dict[str, Any]] = []
        self.rows: list[dict[str, Any]] = []
        self._link: dict[str, Any] | None = None
        self._row: dict[str, Any] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = _attributes(attrs)
        if tag == "a":
            self._link = {"attrs": attributes, "text_parts": []}
        elif tag == "tr":
            self._row = {"attrs": attributes, "cells": [], "links": []}
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link is not None:
            link = {
                "attrs": self._link["attrs"],
                "text": _normalize_text("".join(self._link["text_parts"])),
            }
            self.links.append(link)
            if self._row is not None:
                self._row["links"].append(link)
            self._link = None
        elif tag in {"td", "th"} and self._cell is not None:
            if self._row is not None:
                self._row["cells"].append(_normalize_text("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._row["text"] = _normalize_text(" ".join(self._row["cells"]))
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._link is not None:
            self._link["text_parts"].append(data)
        if self._cell is not None:
            self._cell.append(data)

    @property
    def text(self) -> str:
        return _normalize_text(" ".join(self.text_parts))


class DownloadFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.action: str | None = None
        self.inputs: dict[str, str] = {}
        self._inside_download_form = False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = _attributes(attrs)
        if tag == "form" and attributes.get("id") == "download-form":
            self._inside_download_form = True
            self.action = attributes.get("action")
        elif tag == "input" and self._inside_download_form:
            name = attributes.get("name")
            if name:
                self.inputs[name] = attributes.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._inside_download_form:
            self._inside_download_form = False


@dataclass(frozen=True)
class DiscoveredSource:
    collection_id: str
    collection_name: str
    collection_version: str
    first_year: int
    latest_year: int
    source_publication_date: str | None
    statistics_identifier: str
    statistics_url: str
    legend_url: str
    discovery_mode: str
    earth_engine_asset: str | None
    urban_class_id: int


@dataclass(frozen=True)
class FetchedPage:
    url: str
    body: bytes
    content_type: str | None
    sha256: str


@dataclass(frozen=True)
class AcquiredResource:
    manifest: dict[str, Any]
    artifact_path: Path
    extracted_path: Path | None = None


def _request(url: str) -> Request:
    return Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "antes-da-chuva-mapbiomas/1.0",
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


def _decode_html(page: FetchedPage) -> str:
    charset_match = re.search(r"charset=([\w-]+)", page.content_type or "", re.I)
    charset = charset_match.group(1) if charset_match else "utf-8"
    return page.body.decode(charset)


def _parse_page(page: FetchedPage) -> PageParser:
    parser = PageParser()
    parser.feed(_decode_html(page))
    return parser


def _single(values: list[Any], description: str) -> Any:
    if len(values) != 1:
        raise RuntimeError(
            f"Descoberta MapBiomas sem confianca: esperava 1 {description}, "
            f"encontrei {len(values)}"
        )
    return values[0]


def _parse_publication(value: str) -> tuple[str, str | None]:
    version_match = re.search(r"\b(v\d+(?:\.\d+)*)\b", value, re.I)
    if not version_match:
        raise RuntimeError(f"Versao da tabela MapBiomas nao reconhecida: {value!r}")
    date_match = re.search(
        r"(\d{1,2})\s+de\s+([A-Za-zÀ-ÿ]+)\s+de\s+(\d{4})", value, re.I
    )
    publication_date = None
    if date_match:
        month_name = _ascii_lower(date_match.group(2))
        if month_name not in MONTHS_PT:
            raise RuntimeError(f"Mes de publicacao nao reconhecido: {date_match.group(2)}")
        publication_date = date(
            int(date_match.group(3)),
            MONTHS_PT[month_name],
            int(date_match.group(1)),
        ).isoformat()
    return version_match.group(1).lower(), publication_date


def discover_mapbiomas_sources(
    *,
    coverage_page: FetchedPage,
    statistics_page: FetchedPage,
    legend_page: FetchedPage,
    urbanization_page: FetchedPage,
) -> DiscoveredSource:
    coverage = _parse_page(coverage_page)
    statistics = _parse_page(statistics_page)
    legend = _parse_page(legend_page)
    urbanization = _parse_page(urbanization_page)

    collection_matches = re.findall(
        r"A cole[cç][aã]o mais recente deste produto [ée] a Cole[cç][aã]o\s+"
        r"(\d+(?:\.\d+)?).*?s[ée]rie hist[óo]rica de\s+(\d{4})\s+a\s+(\d{4})",
        coverage.text,
        re.I,
    )
    collection_id, first_year, latest_year = _single(
        collection_matches, "declaracao de colecao vigente"
    )
    collection_name = f"Coleção {collection_id}"
    identifier = f"MAPBIOMAS_BRAZIL-COL.{collection_id}-BIOME_STATE_MUNICIPALITY"

    metadata_rows = [
        row
        for row in coverage.rows
        if row["cells"] and row["cells"][0] == identifier
    ]
    metadata_row = _single(metadata_rows, f"linha de metadata para {identifier}")
    if len(metadata_row["cells"]) != 4:
        raise RuntimeError(
            f"Schema da tabela de descoberta mudou para {identifier}: "
            f"{metadata_row['cells']}"
        )
    collection_version, publication_date = _parse_publication(
        metadata_row["cells"][3]
    )

    coverage_links = [
        link["attrs"]["href"]
        for link in coverage.links
        if link["text"] == identifier and link["attrs"].get("href")
    ]
    coverage_statistics_url = _single(
        coverage_links, f"link oficial para {identifier}"
    )

    statistics_rows = [
        row
        for row in statistics.rows
        if row["attrs"].get("data-colecao") == collection_name
        and row["attrs"].get("data-iniciativa") == "Cobertura 30m"
        and "biomas, estados e municipios" in _ascii_lower(row["text"])
    ]
    statistics_row = _single(
        statistics_rows, "linha municipal na pagina oficial de estatisticas"
    )
    statistics_links = [
        link["attrs"]["href"]
        for link in statistics_row["links"]
        if link["attrs"].get("title") == "Baixar"
        and link["attrs"].get("href")
    ]
    statistics_url = _single(
        statistics_links, "link municipal na pagina oficial de estatisticas"
    )
    if statistics_url != coverage_statistics_url:
        raise RuntimeError(
            "As paginas oficiais do MapBiomas apontam para URLs estatisticas diferentes"
        )

    legend_rows = [
        row
        for row in legend.rows
        if row["attrs"].get("data-colecao") == collection_name
        and "cobertura - codigos de legenda para uso no r ou python"
        in _ascii_lower(row["text"])
        and "mapbiomas brasil (30m)" in _ascii_lower(row["text"])
    ]
    legend_row = _single(legend_rows, "linha da legenda oficial para R/Python")
    legend_links = [
        link["attrs"]["href"]
        for link in legend_row["links"]
        if link["attrs"].get("title") == "Baixar"
        and link["attrs"].get("href")
    ]
    legend_url = _single(legend_links, "link da legenda oficial para R/Python")

    asset_match = re.search(
        rf"projects/mapbiomas-public/assets/[^\s<]*collection{re.escape(collection_id)}[^\s<]*",
        _decode_html(coverage_page),
        re.I,
    )
    urban_class_matches = re.findall(
        r"classe correspondente as areas urbanizadas e a de id\s*[^0-9]*(\d+)",
        _ascii_lower(urbanization.text),
    )
    urban_class_id = int(
        _single(urban_class_matches, "identificador oficial da classe urbanizada")
    )

    statistics_override = os.environ.get("MAPBIOMAS_STATISTICS_URL")
    legend_override = os.environ.get("MAPBIOMAS_LEGEND_URL")
    return DiscoveredSource(
        collection_id=collection_id,
        collection_name=collection_name,
        collection_version=collection_version,
        first_year=int(first_year),
        latest_year=int(latest_year),
        source_publication_date=publication_date,
        statistics_identifier=identifier,
        statistics_url=statistics_override or statistics_url,
        legend_url=legend_override or legend_url,
        discovery_mode="override"
        if statistics_override or legend_override
        else "automatic",
        earth_engine_asset=asset_match.group(0).rstrip('"\'') if asset_match else None,
        urban_class_id=urban_class_id,
    )


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def preserve_discovery_pages(
    *,
    raw_collection_root: Path,
    pages: dict[str, FetchedPage],
) -> dict[str, dict[str, Any]]:
    result = {}
    for name, page in pages.items():
        path = (
            raw_collection_root
            / "discovery"
            / page.sha256[:12]
            / f"{name}.html"
        )
        if not path.exists():
            _atomic_write(path, page.body)
        result[name] = {
            "url": page.url,
            "sha256": page.sha256,
            "content_type": page.content_type,
            "path": str(path),
        }
    return result


def _confirmed_download_response(url: str, timeout_seconds: int):
    response = urlopen(_request(url), timeout=timeout_seconds)
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.casefold():
        return response

    warning_body = response.read()
    warning_url = response.geturl()
    response.close()
    parser = DownloadFormParser()
    parser.feed(warning_body.decode("utf-8"))
    if not parser.action or not parser.inputs:
        raise RuntimeError(
            "O download MapBiomas resolveu para HTML sem o formulario esperado; "
            f"URL final: {warning_url}"
        )
    confirmation_url = urljoin(warning_url, parser.action)
    separator = "&" if "?" in confirmation_url else "?"
    confirmation_url = confirmation_url + separator + urlencode(parser.inputs)
    confirmed = urlopen(_request(confirmation_url), timeout=timeout_seconds)
    confirmed_type = confirmed.headers.get("Content-Type", "")
    if "text/html" in confirmed_type.casefold():
        confirmed.close()
        raise RuntimeError("O Google Drive nao entregou o arquivo apos confirmacao")
    return confirmed


def _filename_from_response(response, fallback_url: str) -> str:
    filename = response.headers.get_filename()
    if filename:
        return Path(filename).name
    fallback = Path(urlparse(fallback_url).path).name
    if not fallback:
        raise RuntimeError("A fonte nao informou um nome de arquivo")
    return fallback


def _stream_download(
    url: str,
    temporary_path: Path,
    *,
    timeout_seconds: int,
) -> tuple[dict[str, Any], str, int]:
    temporary_path.parent.mkdir(parents=True, exist_ok=True)
    if temporary_path.exists():
        temporary_path.unlink()
    digest = hashlib.sha256()
    size = 0
    with _confirmed_download_response(url, timeout_seconds) as response:
        headers = response.headers
        filename = _filename_from_response(response, url)
        resolved_url = response.geturl()
        status = response.status
        with temporary_path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        response_metadata = {
            "resolved_download_url": resolved_url,
            "original_filename": filename,
            "http_status": status,
            "content_type": headers.get("Content-Type"),
            "content_length": int(headers.get("Content-Length"))
            if headers.get("Content-Length")
            else size,
            "etag": headers.get("ETag"),
            "last_modified": headers.get("Last-Modified"),
        }
    return response_metadata, digest.hexdigest(), size


def _load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    _atomic_write(
        path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def _extract_statistics_archive(
    archive_path: Path,
    destination_dir: Path,
) -> tuple[Path, list[dict[str, Any]], str]:
    if not zipfile.is_zipfile(archive_path):
        raise RuntimeError(f"O arquivo estatistico nao e um ZIP valido: {archive_path}")
    members: list[dict[str, Any]] = []
    xlsx_members = []
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            members.append(
                {
                    "filename": info.filename,
                    "file_size": info.file_size,
                    "compressed_size": info.compress_size,
                    "crc": info.CRC,
                }
            )
            if not info.is_dir() and info.filename.casefold().endswith(".xlsx"):
                xlsx_members.append(info)
        member = _single(xlsx_members, "planilha XLSX dentro do ZIP estatistico")
        if Path(member.filename).name != member.filename:
            raise RuntimeError("O ZIP estatistico contem caminho XLSX nao seguro")
        extracted_path = destination_dir / member.filename
        if not extracted_path.exists():
            temporary_path = extracted_path.with_suffix(".xlsx.tmp")
            with archive.open(member) as source, temporary_path.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            temporary_path.replace(extracted_path)
    extracted_sha256 = hashlib.sha256(extracted_path.read_bytes()).hexdigest()
    return extracted_path, members, extracted_sha256


def acquire_resource(
    *,
    resource_type: str,
    source: DiscoveredSource,
    discovery_url: str,
    download_url: str,
    raw_collection_root: Path,
    downloaded_at: datetime,
    timeout_seconds: int = 180,
) -> AcquiredResource:
    if resource_type not in {"statistics", "legend"}:
        raise ValueError(f"Tipo de recurso MapBiomas invalido: {resource_type}")
    resource_root = raw_collection_root / resource_type
    temporary_path = resource_root / ".download.tmp"
    response_metadata, sha256, actual_size = _stream_download(
        download_url,
        temporary_path,
        timeout_seconds=timeout_seconds,
    )
    original_filename = response_metadata["original_filename"]
    artifact_dir = resource_root / sha256[:12]
    artifact_path = artifact_dir / original_filename
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if artifact_path.exists():
        if hashlib.sha256(artifact_path.read_bytes()).hexdigest() != sha256:
            raise RuntimeError(f"Colisao de hash no RAW MapBiomas: {artifact_path}")
        temporary_path.unlink()
    else:
        temporary_path.replace(artifact_path)

    archive_members = None
    extracted_path = None
    extracted_sha256 = None
    if resource_type == "statistics":
        extracted_path, archive_members, extracted_sha256 = _extract_statistics_archive(
            artifact_path, artifact_dir
        )
    else:
        first_bytes = artifact_path.read_bytes()[:256].lstrip()
        if first_bytes.startswith(b"<") or b"class_id" not in first_bytes:
            raise RuntimeError("A legenda baixada nao possui o CSV oficial esperado")

    manifest_path = raw_collection_root / "manifests" / f"{resource_type}.json"
    previous = _load_manifest(manifest_path)
    checks = previous.get("checks", []) if previous else []
    checks.append(
        {
            "checked_at": downloaded_at.isoformat(),
            "sha256": sha256,
            "download_url": download_url,
            "unchanged": bool(previous and previous.get("sha256") == sha256),
        }
    )
    manifest = {
        "source_name": "MapBiomas Brasil",
        "source_product": "Cobertura e Uso da Terra - Cobertura 30m",
        "resource_type": resource_type,
        "discovery_url": discovery_url,
        "discovery_mode": source.discovery_mode,
        "discovered_download_url": download_url,
        **response_metadata,
        "content_length": actual_size,
        "sha256": sha256,
        "downloaded_at": previous.get("downloaded_at")
        if previous and previous.get("sha256") == sha256
        else downloaded_at.isoformat(),
        "last_checked_at": downloaded_at.isoformat(),
        "collection_id": source.collection_id,
        "collection_name": source.collection_name,
        "collection_version": source.collection_version,
        "source_publication_date": source.source_publication_date
        if resource_type == "statistics"
        else None,
        "statistics_publication_date": source.source_publication_date,
        "artifact_path": str(artifact_path),
        "archive_members": archive_members,
        "extracted_path": str(extracted_path) if extracted_path else None,
        "extracted_sha256": extracted_sha256,
        "checks": checks,
    }
    _write_manifest(manifest_path, manifest)
    return AcquiredResource(
        manifest=manifest,
        artifact_path=artifact_path,
        extracted_path=extracted_path,
    )


def discover_and_acquire(
    *,
    coverage_url: str,
    statistics_discovery_url: str,
    legend_discovery_url: str,
    urbanization_url: str,
    raw_root: Path,
    downloaded_at: datetime,
) -> tuple[
    DiscoveredSource,
    AcquiredResource,
    AcquiredResource,
    dict[str, dict[str, Any]],
]:
    pages = {
        "coverage": fetch_page(coverage_url),
        "statistics": fetch_page(statistics_discovery_url),
        "legend": fetch_page(legend_discovery_url),
        "urbanization": fetch_page(urbanization_url),
    }
    source = discover_mapbiomas_sources(
        coverage_page=pages["coverage"],
        statistics_page=pages["statistics"],
        legend_page=pages["legend"],
        urbanization_page=pages["urbanization"],
    )
    collection_root = raw_root / f"collection_{source.collection_id}"
    discovery_manifest = preserve_discovery_pages(
        raw_collection_root=collection_root,
        pages=pages,
    )
    statistics = acquire_resource(
        resource_type="statistics",
        source=source,
        discovery_url=statistics_discovery_url,
        download_url=source.statistics_url,
        raw_collection_root=collection_root,
        downloaded_at=downloaded_at,
    )
    legend = acquire_resource(
        resource_type="legend",
        source=source,
        discovery_url=legend_discovery_url,
        download_url=source.legend_url,
        raw_collection_root=collection_root,
        downloaded_at=downloaded_at,
    )
    return source, statistics, legend, discovery_manifest
