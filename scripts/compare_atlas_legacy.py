"""Compare the legacy Atlas presentation metrics with canonical GOLD facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import duckdb


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from src.config import ATLAS_FACT_PATH, GOLD_PARQUET_PATH, PROJECT_ROOT


LEGACY_TYPE_LABELS = {
    1: "Alagamentos",
    2: "Enxurradas",
    7: "Inundações",
    8: "Movimento de massa",
    13: "Chuvas intensas",
}
METRICS = (
    "records",
    "recognized",
    "firstYear",
    "lastYear",
    "deaths",
    "injured",
    "displaced",
    "missing",
    "types",
    "years",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _legacy_metrics(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for row in rows:
        history = row["history"]
        result[row["code"]] = history or {
            "records": 0,
            "recognized": 0,
            "firstYear": None,
            "lastYear": None,
            "deaths": 0,
            "injured": 0,
            "displaced": 0,
            "missing": 0,
            "types": {},
            "years": {},
        }
    return result


def _canonical_metrics(path: Path, dim_path: Path) -> dict[str, dict[str, Any]]:
    connection = duckdb.connect(":memory:")
    escaped = str(path).replace("'", "''")
    escaped_dim = str(dim_path).replace("'", "''")
    result = {
        row[0]: {
            "records": 0,
            "recognized": 0,
            "firstYear": None,
            "lastYear": None,
            "deaths": 0,
            "injured": 0,
            "displaced": 0,
            "missing": 0,
            "types": {},
            "years": {},
        }
        for row in connection.execute(
            f"SELECT codigo_ibge FROM read_parquet('{escaped_dim}')"
        ).fetchall()
    }
    rows = connection.execute(
        f"""
        SELECT
            codigo_ibge,
            count(*) AS records,
            count(*) FILTER (WHERE is_federally_recognized) AS recognized,
            min(event_year) AS first_year,
            max(event_year) AS last_year,
            sum(deaths) AS deaths,
            sum(injured) AS injured,
            sum(homeless + displaced) AS displaced,
            sum(missing) AS missing
        FROM read_parquet('{escaped}')
        WHERE is_rain_related
        GROUP BY codigo_ibge
        """
    ).fetchall()
    for row in rows:
        result[row[0]] = {
            "records": row[1],
            "recognized": row[2],
            "firstYear": row[3],
            "lastYear": row[4],
            "deaths": row[5],
            "injured": row[6],
            "displaced": row[7],
            "missing": row[8],
            "types": Counter(),
            "years": Counter(),
        }
    type_rows = connection.execute(
        f"""
        SELECT codigo_ibge, atlas_type_id, event_year, count(*)
        FROM read_parquet('{escaped}')
        WHERE is_rain_related
        GROUP BY codigo_ibge, atlas_type_id, event_year
        """
    ).fetchall()
    connection.close()
    for code, atlas_type_id, year, count in type_rows:
        record = result[code]
        record["types"][LEGACY_TYPE_LABELS[atlas_type_id]] += count
        record["years"][str(year)] += count
    for record in result.values():
        record["types"] = dict(
            sorted(record["types"].items(), key=lambda item: (-item[1], item[0]))
        )
        record["years"] = dict(sorted(record["years"].items()))
    return result


def compare(legacy_path: Path, fact_path: Path, dim_path: Path) -> dict[str, Any]:
    legacy = _legacy_metrics(legacy_path)
    canonical = _canonical_metrics(fact_path, dim_path)
    common_codes = sorted(set(legacy) & set(canonical))
    differences = []
    for code in common_codes:
        different_metrics = {
            metric: {"legacy": legacy[code][metric], "canonical": canonical[code][metric]}
            for metric in METRICS
            if legacy[code][metric] != canonical[code][metric]
        }
        if different_metrics:
            differences.append({"codigo_ibge": code, "metrics": different_metrics})
    return {
        "legacy_sha256": _sha256(legacy_path),
        "canonical_fact_sha256": _sha256(fact_path),
        "legacy_municipalities": len(legacy),
        "canonical_dimension_municipalities": len(canonical),
        "common_codes": len(common_codes),
        "legacy_only_codes": sorted(set(legacy) - set(canonical)),
        "canonical_only_codes": sorted(set(canonical) - set(legacy)),
        "legacy_rain_records": sum(item["records"] for item in legacy.values()),
        "canonical_rain_records": sum(item["records"] for item in canonical.values()),
        "legacy_municipalities_with_rain_records": sum(
            item["records"] > 0 for item in legacy.values()
        ),
        "canonical_municipalities_with_rain_records": sum(
            item["records"] > 0 for item in canonical.values()
        ),
        "difference_count": len(differences),
        "differences": differences,
    }


def render_markdown(result: dict[str, Any]) -> str:
    if result["differences"]:
        difference_section = "\n".join(
            f"| `{item['codigo_ibge']}` | {', '.join(item['metrics'])} |"
            for item in result["differences"]
        )
    else:
        difference_section = "Nenhuma diferenca encontrada nos codigos comuns."
    return f"""# Relatorio de Paridade Atlas

Comparacao executada pelo `scripts/compare_atlas_legacy.py` entre o Atlas do
payload publicado legado e `fact_disaster_event.parquet` canonica.

## Entradas

- Payload legado: `app/public/data/municipios.json`, SHA-256
  `{result['legacy_sha256']}`.
- FACT Atlas GOLD: `data/gold/fact_disaster_event.parquet`, SHA-256
  `{result['canonical_fact_sha256']}`.

## Resultado

| Medida | Legado | Canonico |
|---|---:|---:|
| Municipios no universo comparado | {result['legacy_municipalities']} | {result['canonical_dimension_municipalities']} na dimensao vigente |
| Codigos comuns | {result['common_codes']} | {result['common_codes']} |
| Municipios com registros no recorte de chuva | {result['legacy_municipalities_with_rain_records']} | {result['canonical_municipalities_with_rain_records']} |
| Registros nas cinco tipologias | {result['legacy_rain_records']} | {result['canonical_rain_records']} |
| Diferencas por codigo/metricas | {result['difference_count']} | {result['difference_count']} |

Os dez campos comparados para cada codigo comum foram `records`, `recognized`,
`firstYear`, `lastYear`, `deaths`, `injured`, `displaced`, `missing`, `types` e
`years`. `displaced` no canonico e a soma de `homeless + displaced`, que e a
mesma regra do payload legado. A selecao usa `is_rain_related` da classificacao
canonizada e as cinco tipologias Atlas 1, 2, 7, 8 e 13; tambem foram comparadas
as contagens por tipologia e por ano.

## Diferencas dos codigos comuns

{difference_section}

## Diferenca de universo

O legado possui 5.570 codigos porque usa a referencia Censo 2022. A dimensao
IBGE vigente possui 5.571 e inclui Boa Esperanca do Norte/MT (`5101837`), que
nao esta no payload legado. Ela nao e uma divergencia Atlas: nao existe registro
legado para comparar. O exportador a inclui no indice canonico e marca Censo e
Transferegov como `not_in_legacy_universe` ate que suas fontes tenham pipelines
canonicos.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--legacy",
        type=Path,
        default=PROJECT_ROOT / "app" / "public" / "data" / "municipios.json",
    )
    parser.add_argument("--fact", type=Path, default=ATLAS_FACT_PATH)
    parser.add_argument("--dim", type=Path, default=GOLD_PARQUET_PATH)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "docs" / "RELATORIO_PARIDADE_ATLAS.md"
    )
    args = parser.parse_args()
    result = compare(args.legacy, args.fact, args.dim)
    args.output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
