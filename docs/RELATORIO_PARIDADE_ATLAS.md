# Relatorio de Paridade Atlas

Comparacao executada pelo `scripts/compare_atlas_legacy.py` entre o Atlas do
payload publicado legado e `fact_disaster_event.parquet` canonica.

## Entradas

- Payload legado: `app/public/data/municipios.json`, SHA-256
  `d27d90d50175f506375785d05f68394c1b9f118f2b9d57077b8f000cfa4384bf`.
- FACT Atlas GOLD: `data/gold/fact_disaster_event.parquet`, SHA-256
  `c74c4ed0c48cb7bcdc1ee78b75fc0f9c25dade813d9c4cce55854f8b20cb43e8`.

## Resultado

| Medida | Legado | Canonico |
|---|---:|---:|
| Municipios no universo comparado | 5570 | 5571 na dimensao vigente |
| Codigos comuns | 5570 | 5570 |
| Municipios com registros no recorte de chuva | 4708 | 4708 |
| Registros nas cinco tipologias | 29352 | 29352 |
| Diferencas por codigo/metricas | 0 | 0 |

Os dez campos comparados para cada codigo comum foram `records`, `recognized`,
`firstYear`, `lastYear`, `deaths`, `injured`, `displaced`, `missing`, `types` e
`years`. `displaced` no canonico e a soma de `homeless + displaced`, que e a
mesma regra do payload legado. A selecao usa `is_rain_related` da classificacao
canonizada e as cinco tipologias Atlas 1, 2, 7, 8 e 13; tambem foram comparadas
as contagens por tipologia e por ano.

## Diferencas dos codigos comuns

Nenhuma diferenca encontrada nos codigos comuns.

## Diferenca de universo

O legado possui 5.570 codigos porque usa a referencia Censo 2022. A dimensao
IBGE vigente possui 5.571 e inclui Boa Esperanca do Norte/MT (`5101837`), que
nao esta no payload legado. Ela nao e uma divergencia Atlas: nao existe registro
legado para comparar. O exportador a inclui no indice canonico e marca Censo e
Transferegov como `not_in_legacy_universe` ate que suas fontes tenham pipelines
canonicos.
