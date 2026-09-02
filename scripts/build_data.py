"""Gera o conjunto municipal compacto usado pelo MVP.

Entradas esperadas (não versionadas):
  data/raw/atlas_1991_2025.xlsx
  data/raw/censo_6805_percentual_rede.json

Saída versionável:
  app/public/data/municipios.json
"""

from __future__ import annotations

import json
import math
import re
import sys
import zipfile
import csv
import io
import unicodedata
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / "data" / "raw" / "atlas_1991_2025.xlsx"
CENSO_PATH = ROOT / "data" / "raw" / "censo_6805_percentual_rede.json"
OUTPUT_PATH = ROOT / "app" / "public" / "data" / "municipios.json"
PROGRAM_ZIP = ROOT / "data" / "raw" / "siconv_programa.csv.zip"
PROGRAM_PROPOSAL_ZIP = (
    ROOT / "data" / "raw" / "siconv_programa_proposta.csv.zip"
)
PROPOSAL_ZIP = ROOT / "data" / "raw" / "siconv_proposta.csv.zip"
AGREEMENT_ZIP = ROOT / "data" / "raw" / "siconv_convenio.csv.zip"

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

RAIN_TYPES = {
    "1": "Alagamentos",
    "2": "Enxurradas",
    "7": "Inundações",
    "8": "Movimento de massa",
    "13": "Chuvas intensas",
}


def qname(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    strings: list[str] = []
    with archive.open("xl/sharedStrings.xml") as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag == qname(NS_MAIN, "si"):
                strings.append(
                    "".join(
                        node.text or ""
                        for node in element.iter(qname(NS_MAIN, "t"))
                    )
                )
                element.clear()
    return strings


def workbook_sheets(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    relations_root = ET.parse(
        archive.open("xl/_rels/workbook.xml.rels")
    ).getroot()
    relations = {
        relation.attrib["Id"]: relation.attrib["Target"]
        for relation in relations_root.findall(qname(NS_PKG_REL, "Relationship"))
    }
    workbook_root = ET.parse(archive.open("xl/workbook.xml")).getroot()
    sheets: list[dict[str, str]] = []
    sheets_element = workbook_root.find(qname(NS_MAIN, "sheets"))
    for sheet in list(sheets_element) if sheets_element is not None else []:
        relation_id = sheet.attrib[qname(NS_REL, "id")]
        target = relations[relation_id].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheets.append({"name": sheet.attrib["name"], "path": target})
    return sheets


def column_number(cell_reference: str) -> int:
    number = 0
    for character in cell_reference:
        if not character.isalpha():
            break
        number = number * 26 + ord(character.upper()) - 64
    return number - 1


def cell_value(cell: ET.Element, shared_strings: list[str]):
    value = cell.find(qname(NS_MAIN, "v"))
    if value is None:
        inline = cell.find(qname(NS_MAIN, "is"))
        if inline is None:
            return None
        return "".join(
            node.text or "" for node in inline.iter(qname(NS_MAIN, "t"))
        )
    raw = value.text
    if cell.attrib.get("t") == "s":
        return shared_strings[int(raw)]
    if cell.attrib.get("t") == "b":
        return raw == "1"
    return raw


def read_rows(
    archive: zipfile.ZipFile, path: str, shared_strings: list[str]
):
    with archive.open(path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != qname(NS_MAIN, "row"):
                continue
            values = {}
            for cell in element.findall(qname(NS_MAIN, "c")):
                values[column_number(cell.attrib["r"])] = cell_value(
                    cell, shared_strings
                )
            width = max(values, default=-1) + 1
            yield [values.get(index) for index in range(width)]
            element.clear()


def row_value(row: list, index: int | None):
    if index is None or index >= len(row):
        return None
    return row[index]


def numeric(value) -> int:
    if value in (None, ""):
        return 0
    try:
        number = float(str(value).replace(",", "."))
        return int(round(number)) if math.isfinite(number) else 0
    except ValueError:
        return 0


def event_year(value) -> int | None:
    try:
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).year
    except (TypeError, ValueError, OverflowError):
        return None


@contextmanager
def zipped_csv(path: Path):
    with zipfile.ZipFile(path) as archive:
        csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(csv_name) as binary_stream:
            with io.TextIOWrapper(
                binary_stream, encoding="utf-8-sig", errors="replace", newline=""
            ) as text_stream:
                yield csv.DictReader(text_stream, delimiter=";")


def decimal_value(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return round(float(value.replace(".", "").replace(",", ".")), 2)
    except ValueError:
        return None


def normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def object_mentions_municipality(
    object_text: str, municipality_name: str, uf: str
) -> bool:
    normalized_object = normalized_text(object_text)
    normalized_name = normalized_text(municipality_name)
    candidates = (
        f"municipio de {normalized_name}",
        f"municipio do {normalized_name}",
        f"municipio da {normalized_name}",
        f"{normalized_name} {uf.casefold()}",
    )
    return any(candidate in normalized_object for candidate in candidates)


def transferegov_aggregates(
    municipality_names: dict[str, tuple[str, str]]
) -> dict[str, dict]:
    required = (PROGRAM_ZIP, PROGRAM_PROPOSAL_ZIP, PROPOSAL_ZIP, AGREEMENT_ZIP)
    if not all(path.exists() for path in required):
        return {}

    program_actions: dict[str, set[str]] = {}
    with zipped_csv(PROGRAM_ZIP) as rows:
        for row in rows:
            name = (row.get("NOME_PROGRAMA") or "").casefold()
            action = (row.get("ACAO_ORCAMENTARIA") or "").strip().upper()
            legacy = all(term in name for term in ("preven", "prepara", "desastr"))
            current = (
                all(term in name for term in ("gest", "riscos", "desastres"))
                and any(action.endswith(code) for code in ("8172", "8865", "00TK", "00T5"))
            )
            if not (legacy or current):
                continue
            program_id = str(row.get("ID_PROGRAMA") or "")
            if not program_id:
                continue
            program_actions.setdefault(program_id, set()).add(
                next(
                    (code for code in ("8172", "8865", "00TK", "00T5") if action.endswith(code)),
                    "prevenção/preparação",
                )
            )

    proposal_actions: dict[str, set[str]] = {}
    with zipped_csv(PROGRAM_PROPOSAL_ZIP) as rows:
        for row in rows:
            program_id = str(row.get("ID_PROGRAMA") or "")
            if program_id not in program_actions:
                continue
            proposal_id = str(row.get("ID_PROPOSTA") or "")
            if proposal_id:
                proposal_actions.setdefault(proposal_id, set()).update(
                    program_actions[program_id]
                )

    proposals: dict[str, dict] = {}
    with zipped_csv(PROPOSAL_ZIP) as rows:
        for row in rows:
            proposal_id = str(row.get("ID_PROPOSTA") or "")
            if proposal_id not in proposal_actions:
                continue
            municipality_code = str(row.get("COD_MUNIC_IBGE") or "")
            if not re.fullmatch(r"\d{7}", municipality_code):
                continue
            proposals[proposal_id] = {
                "municipalityCode": municipality_code,
                "object": (row.get("OBJETO_PROPOSTA") or "").strip(),
                "proposalYear": numeric(row.get("ANO_PROP")),
                "actions": proposal_actions[proposal_id],
            }

    aggregates: dict[str, dict] = {}
    seen_agreements: set[str] = set()
    with zipped_csv(AGREEMENT_ZIP) as rows:
        for row in rows:
            proposal_id = str(row.get("ID_PROPOSTA") or "")
            proposal = proposals.get(proposal_id)
            if proposal is None:
                continue
            code = proposal["municipalityCode"]
            municipality = municipality_names.get(code)
            if municipality is None or not object_mentions_municipality(
                proposal["object"], municipality[0], municipality[1]
            ):
                continue
            agreement_number = str(row.get("NR_CONVENIO") or "")
            if not agreement_number or agreement_number in seen_agreements:
                continue
            seen_agreements.add(agreement_number)

            year = numeric(row.get("ANO")) or proposal["proposalYear"]
            item = aggregates.setdefault(
                code,
                {
                    "agreements": 0,
                    "firstYear": None,
                    "lastYear": None,
                    "actions": set(),
                    "latest": None,
                    "attribution": "objeto menciona o município",
                },
            )
            item["agreements"] += 1
            item["firstYear"] = min(item["firstYear"] or year, year)
            item["lastYear"] = max(item["lastYear"] or year, year)
            item["actions"].update(proposal["actions"])
            if item["latest"] is None or year >= item["latest"]["year"]:
                item["latest"] = {
                    "number": agreement_number,
                    "year": year,
                    "status": (row.get("SIT_CONVENIO") or "").strip(),
                    "object": proposal["object"],
                    "globalValue": decimal_value(row.get("VL_GLOBAL_CONV")),
                }

    for item in aggregates.values():
        item["actions"] = sorted(item["actions"])
    return aggregates


def atlas_aggregates() -> dict[str, dict]:
    aggregates: dict[str, dict] = {}
    with zipfile.ZipFile(ATLAS_PATH) as archive:
        shared_strings = load_shared_strings(archive)
        sheet = next(
            item
            for item in workbook_sheets(archive)
            if "Valores Corrigidos" in item["name"]
        )
        rows = read_rows(archive, sheet["path"], shared_strings)
        headers = next(rows)
        indices = {header: index for index, header in enumerate(headers)}

        for row in rows:
            typology_code = str(row_value(row, indices.get("tipologia")) or "")
            if typology_code not in RAIN_TYPES:
                continue

            municipality_code = str(
                row_value(row, indices.get("Cod_IBGE_Mun")) or ""
            ).strip()
            if not re.fullmatch(r"\d{7}", municipality_code):
                continue

            year = event_year(row_value(row, indices.get("Data_Evento")))
            status = str(row_value(row, indices.get("Status")) or "")
            item = aggregates.setdefault(
                municipality_code,
                {
                    "records": 0,
                    "recognized": 0,
                    "firstYear": None,
                    "lastYear": None,
                    "types": Counter(),
                    "years": Counter(),
                    "deaths": 0,
                    "injured": 0,
                    "displaced": 0,
                    "missing": 0,
                },
            )
            item["records"] += 1
            item["recognized"] += int(status == "Reconhecido")
            item["types"][RAIN_TYPES[typology_code]] += 1
            if year is not None:
                item["years"][str(year)] += 1
                item["firstYear"] = min(item["firstYear"] or year, year)
                item["lastYear"] = max(item["lastYear"] or year, year)
            item["deaths"] += numeric(
                row_value(row, indices.get("DH_MORTOS"))
            )
            item["injured"] += numeric(
                row_value(row, indices.get("DH_FERIDOS"))
            )
            item["displaced"] += numeric(
                row_value(row, indices.get("DH_DESABRIGADOS"))
            ) + numeric(row_value(row, indices.get("DH_DESALOJADOS")))
            item["missing"] += numeric(
                row_value(row, indices.get("DH_DESAPARECIDOS"))
            )

    for item in aggregates.values():
        item["types"] = dict(
            sorted(item["types"].items(), key=lambda value: (-value[1], value[0]))
        )
        item["years"] = dict(sorted(item["years"].items()))
    return aggregates


def parse_municipality(label: str) -> tuple[str, str]:
    match = re.match(r"^(.*) - ([A-Z]{2})$", label)
    if not match:
        raise ValueError(f"Nome municipal inesperado: {label}")
    return match.group(1), match.group(2)


def build_dataset() -> list[dict]:
    atlas = atlas_aggregates()
    censo_rows = json.loads(CENSO_PATH.read_text(encoding="utf-8-sig"))
    municipality_names = {
        str(row["D1C"]): parse_municipality(row["D1N"])
        for row in censo_rows[1:]
    }
    transfers = transferegov_aggregates(municipality_names)
    municipalities = []

    for row in censo_rows[1:]:
        code = str(row["D1C"])
        name, uf = parse_municipality(row["D1N"])
        raw_connected = str(row["V"])
        connected = (
            float(raw_connected)
            if re.fullmatch(r"\d+(?:\.\d+)?", raw_connected)
            else None
        )
        history = atlas.get(code)
        municipalities.append(
            {
                "code": code,
                "name": name,
                "uf": uf,
                "census": {
                    "connectedSewerPct": (
                        round(connected, 2) if connected is not None else None
                    ),
                    "outsideSelectedSewerPct": (
                        round(100 - connected, 2)
                        if connected is not None
                        else None
                    ),
                    "year": 2022,
                },
                "history": history,
                "transfers": transfers.get(code),
            }
        )

    municipalities.sort(key=lambda item: (item["uf"], item["name"].casefold()))
    return municipalities


def main() -> None:
    for path in (ATLAS_PATH, CENSO_PATH):
        if not path.exists():
            print(f"Arquivo ausente: {path}", file=sys.stderr)
            raise SystemExit(1)

    municipalities = build_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(municipalities, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    with_history = [item for item in municipalities if item["history"]]
    with_transfers = [item for item in municipalities if item["transfers"]]
    print(
        json.dumps(
            {
                "municipalities": len(municipalities),
                "withRainHistory": len(with_history),
                "rainRecords": sum(
                    item["history"]["records"] for item in with_history
                ),
                "censusValues": sum(
                    item["census"]["outsideSelectedSewerPct"] is not None
                    for item in municipalities
                ),
                "municipalitiesWithTransfers": len(with_transfers),
                "agreements": sum(
                    item["transfers"]["agreements"] for item in with_transfers
                ),
                "output": str(OUTPUT_PATH),
                "bytes": OUTPUT_PATH.stat().st_size,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
