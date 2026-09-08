# Baseline da Consolidação

Verificações executadas em 3 de setembro de 2026 depois da cópia local das
camadas RAW, SILVER e GOLD para este repositório.

## Frontend

Executados em `app/`, usando as dependências locais já instaladas:

```bash
npm run lint
npm run build
```

Os dois comandos concluíram com sucesso. O build exibiu o aviso do Vinext de que
algumas rotas não puderam ser classificadas pela análise estática; não houve erro
de build. `npm ci` não foi executado nesta verificação.

## Pipeline Python

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python scripts/export_frontend_data.py
python -m pytest -q
```

Resultados observados:

- `python -m src.pipeline`: dimensão IBGE materializada com 5.571 linhas, 27
  UFs e 5 regiões. O relatório `data/gold/data_quality_report.json` terminou em
  `PASS` às `2026-09-03T12:06:12+00:00`.
- `python -m src.mapbiomas`: coleção 11 retornou `NO_CHANGE`, sem reconstruir
  os Parquets já válidos: 2.798.168 linhas FACT e cobertura municipal de
  99,982050%. O manifest da checagem é
  `data/manifests/mapbiomas/20260903T120622Z_118b26e4.json`; o relatório de
  qualidade materializado permanece `PASS`.
- `python -m src.atlas`: release `atlas_1991_2025_v1.1_2026-08-06` terminou em
  `PASS`: 76.190 eventos FACT e cobertura municipal de 94,345719%. O manifest
  da execução é `data/manifests/atlas/20260903T120637Z_b199b23f.json`.
- `python scripts/export_frontend_data.py`: gerou 30 arquivos v1 para 5.571
  municípios e 27 UFs. `metadata.json` tem SHA-256
  `afe0e5ce32a07b7537d2bfdce46d6f88c4e34448c2ddef0f3c86b14b89657e35` e
  `municipal-index.json` tem SHA-256
  `78b3c3d31590491b97d131ea9dd1f28c3dff0144c1d99ca70558561c2d65cdfc`.
- `python -m pytest -q`: `20 passed in 1.70s`.

O relatório de paridade Atlas foi regenerado com a FACT atual: os 5.570 códigos
comuns ao payload legado possuem zero diferenças nas dez métricas comparadas;
os dois lados têm 29.352 registros nas cinco tipologias. A única diferença de
universo é Boa Esperança do Norte/MT (`5101837`), presente apenas na dimensão
IBGE vigente de 5.571 unidades.

## Política de Dados

A auditoria equivalente à etapa `Verificar política de dados` do CI terminou em
`PASS`. O índice Git contém somente `data/raw/.gitkeep` nas camadas locais, sem
RAW, SILVER, GOLD ou Parquet rastreado. Há 26 manifests JSON compactos no
diretório local, totalizando 95.256 bytes; o maior tem 4.621 bytes.

## Clone limpo

Depois de registrar a consolidação em Git, `scripts/verify_clean_clone.sh` foi
executado com sucesso no commit `39581e28fc1748b2f014bdae7a9b10c56b7547ee`.
O clone temporário passou nos testes de exportação (`5 passed`), na suíte Python
(`18 passed, 2 skipped` por dependerem das GOLDs locais), no lint, nos 10 testes
frontend e no build. Consulte [REPRODUCAO.md](REPRODUCAO.md) para o ambiente e
as versões usados.
