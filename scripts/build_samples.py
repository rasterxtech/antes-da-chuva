"""Gera amostras pequenas e versionáveis do conjunto municipal consolidado.

A amostra não substitui as bases oficiais nem deve ser usada para estatísticas
nacionais. Ela existe para exploração, testes e integração por colaboradores.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "app" / "public" / "data" / "municipios.json"
OUTPUT_DIR = ROOT / "data" / "samples"

# Uma capital por UF, o município demonstrador e três casos de borda.
SAMPLE_CODES = (
    "1200401",  # Rio Branco, AC
    "2704302",  # Maceió, AL
    "1600303",  # Macapá, AP
    "1302603",  # Manaus, AM
    "2927408",  # Salvador, BA
    "2304400",  # Fortaleza, CE
    "5300108",  # Brasília, DF
    "3205309",  # Vitória, ES
    "5208707",  # Goiânia, GO
    "2111300",  # São Luís, MA
    "5103403",  # Cuiabá, MT
    "5002704",  # Campo Grande, MS
    "3106200",  # Belo Horizonte, MG
    "1501402",  # Belém, PA
    "2507507",  # João Pessoa, PB
    "4106902",  # Curitiba, PR
    "2611606",  # Recife, PE
    "2211001",  # Teresina, PI
    "3304557",  # Rio de Janeiro, RJ
    "2408102",  # Natal, RN
    "4314902",  # Porto Alegre, RS
    "1100205",  # Porto Velho, RO
    "1400100",  # Boa Vista, RR
    "4205407",  # Florianópolis, SC
    "3550308",  # São Paulo, SP
    "2800308",  # Aracaju, SE
    "1721000",  # Palmas, TO
    "4202404",  # Blumenau, SC: caso demonstrador
    "1200013",  # Acrelândia, AC: sem histórico nem transferência
    "2903953",  # Bom Jesus da Serra, BA: transferência sem histórico
    "2106672",  # Milagres do Maranhão, MA: indicador censitário ausente
)


def write_json(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    municipalities = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    by_code = {item["code"]: item for item in municipalities}
    missing_codes = [code for code in SAMPLE_CODES if code not in by_code]
    if missing_codes:
        raise ValueError(f"Códigos ausentes no conjunto municipal: {missing_codes}")

    sample = sorted(
        (by_code[code] for code in SAMPLE_CODES),
        key=lambda item: (item["uf"], item["name"]),
    )
    if len(sample) != len(set(SAMPLE_CODES)):
        raise ValueError("A lista de municípios da amostra contém duplicatas.")
    if len({item["uf"] for item in sample}) != 27:
        raise ValueError("A amostra deve representar as 27 unidades federativas.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "municipios.sample.json", sample)

    census_rows = [
        {
            "codigo_ibge": item["code"],
            "municipio": item["name"],
            "uf": item["uf"],
            "ano": item["census"]["year"],
            "rede_geral_pct": item["census"]["connectedSewerPct"],
            "fora_formas_selecionadas_pct": item["census"][
                "outsideSelectedSewerPct"
            ],
        }
        for item in sample
    ]
    write_csv(
        OUTPUT_DIR / "censo.sample.csv",
        [
            "codigo_ibge",
            "municipio",
            "uf",
            "ano",
            "rede_geral_pct",
            "fora_formas_selecionadas_pct",
        ],
        census_rows,
    )

    atlas_rows = []
    for item in sample:
        history = item["history"]
        if history is None:
            continue
        atlas_rows.append(
            {
                "codigo_ibge": item["code"],
                "municipio": item["name"],
                "uf": item["uf"],
                "registros": history["records"],
                "reconhecidos": history["recognized"],
                "primeiro_ano": history["firstYear"],
                "ultimo_ano": history["lastYear"],
                "mortos": history["deaths"],
                "feridos": history["injured"],
                "desabrigados_desalojados": history["displaced"],
                "desaparecidos": history["missing"],
                "tipologias_json": compact_json(history["types"]),
                "anos_json": compact_json(history["years"]),
            }
        )
    write_csv(
        OUTPUT_DIR / "atlas.sample.csv",
        [
            "codigo_ibge",
            "municipio",
            "uf",
            "registros",
            "reconhecidos",
            "primeiro_ano",
            "ultimo_ano",
            "mortos",
            "feridos",
            "desabrigados_desalojados",
            "desaparecidos",
            "tipologias_json",
            "anos_json",
        ],
        atlas_rows,
    )

    transfer_rows = []
    for item in sample:
        transfers = item["transfers"]
        if transfers is None:
            continue
        latest = transfers["latest"]
        transfer_rows.append(
            {
                "codigo_ibge": item["code"],
                "municipio": item["name"],
                "uf": item["uf"],
                "convenios": transfers["agreements"],
                "primeiro_ano": transfers["firstYear"],
                "ultimo_ano": transfers["lastYear"],
                "acoes_json": compact_json(transfers["actions"]),
                "numero_mais_recente": latest["number"],
                "ano_mais_recente": latest["year"],
                "situacao_mais_recente": latest["status"],
                "objeto_mais_recente": latest["object"],
                "valor_global_mais_recente": latest["globalValue"],
                "criterio_atribuicao": transfers["attribution"],
            }
        )
    write_csv(
        OUTPUT_DIR / "transferegov.sample.csv",
        [
            "codigo_ibge",
            "municipio",
            "uf",
            "convenios",
            "primeiro_ano",
            "ultimo_ano",
            "acoes_json",
            "numero_mais_recente",
            "ano_mais_recente",
            "situacao_mais_recente",
            "objeto_mais_recente",
            "valor_global_mais_recente",
            "criterio_atribuicao",
        ],
        transfer_rows,
    )

    print(
        "Amostras geradas: "
        f"{len(sample)} municípios, "
        f"{len(atlas_rows)} linhas do Atlas e "
        f"{len(transfer_rows)} linhas do Transferegov."
    )


if __name__ == "__main__":
    main()
