# Contexto comum do projeto

Este prompt pertence ao projeto **Antes da Chuva**, um data product local, reproduzível e auditável para integração de dados públicos brasileiros por município.

Já existem e estão validados:

- `dim_municipality`, baseada no IBGE;
- pipeline MapBiomas;
- `fact_municipality_land_cover`;
- `snapshot_municipality_land_cover`;
- `municipality_land_cover_change`;
- RAW, SILVER e GOLD;
- manifests, data quality reports, testes, idempotência, versionamento por hash e matching territorial por `codigo_ibge`.

## Contrato arquitetural

- `codigo_ibge` é a chave territorial canônica.
- Nome de município nunca substitui código oficial quando o código existir.
- Python padrão + DuckDB.
- RAW preserva bytes originais, headers, URL de descoberta, URL resolvida, nome original, tamanho, SHA-256, ETag, Last-Modified, data oficial da fonte quando houver, timestamp de ingestão e versão/release/ciclo.
- SILVER normaliza sem apagar divergências úteis para auditoria.
- GOLD publica estruturas analíticas com granularidade explícita.
- Toda GOLD deve ter linhagem suficiente para chegar ao RAW correspondente.
- Mudanças de schema devem falhar explicitamente.
- Execução idêntica deve resultar em `NO_CHANGE`.
- Não criar score de risco, ranking, probabilidade de enchente ou causalidade.
- Ausência de registro em uma fonte não significa ausência do fenômeno.

## Manifest por fonte

Criar `data/manifests/<source>/latest_successful_run.json` com: `run_id`, `source`, `source_release`, `started_at`, `finished_at`, `discovery_urls`, `resolved_urls`, `source_hashes`, `rows_raw`, `rows_silver`, `rows_gold`, `municipality_coverage_pct`, `schema_fingerprint`, `pipeline_fingerprint`, `status`.

Status: `PASS`, `NO_CHANGE`, `BLOCKED_SOURCE`, `FAILED`.

## Contrato de schema

Criar `src/contracts/<source>.py` com `required_fields`, `optional_fields`, `known_variants` e `unexpected_fields` quando aplicável. Nunca adaptar silenciosamente mudanças relevantes da fonte.

# Prompt — Indicador de Capacidade Municipal (ICM)

## Objetivo
Implementar o ICM como fonte oficial de capacidade institucional municipal. Pergunta: **que capacidade institucional foi declarada/mensurada oficialmente?** Não criar índice próprio.

## Fonte oficial
https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/icm

Descobrir Base Completa, XLS, PDF metodológico, arquivos por faixa, variáveis, dimensões e ciclo atual. Não hardcode links finais.

## Temporalidade
Tratar por ciclos/snapshots e criar `icm_cycle_id`. Nunca sobrescrever ciclos antigos. Não presumir comparabilidade se a metodologia mudar.

## RAW
`data/raw/icm/discovery/` e `data/raw/icm/<cycle>/`. Preservar resultados e metodologia.

## SILVER
1. `silver_icm_municipality`: `icm_cycle + codigo_ibge`, preservando o snapshot original.
2. `silver_icm_variable`: `icm_cycle + codigo_ibge + variable_id`, com nome, dimensão, valor bruto/normalizado, hash e ingestão. Se a fonte não tiver IDs, criar IDs técnicos determinísticos e documentados.

## GOLDs
1. `snapshot_municipality_capacity`: `codigo_ibge + icm_cycle`, publicando somente score/faixa/dimensões oficiais existentes. Não reconstruir pesos.
2. `fact_municipality_capacity_item`: `codigo_ibge + icm_cycle + variable_id`.
3. `municipality_capacity_change`: somente com dois ciclos; incluir ciclo anterior/atual, faixa anterior/atual, mudança de faixa, variáveis adquiridas/perdidas e `methodology_comparable`. Se false, não rotular melhorou/piorou.

## Matching e DQ
Associar por código IBGE. Reportar cobertura e códigos sem match. Validar unicidade município/ciclo, município/ciclo/variável, domínio de score/faixa, dimensões conhecidas e mudanças metodológicas.

## Atualização
Ao detectar novo ciclo: preservar anterior, baixar novo RAW, comparar schema/metodologia, gerar novo snapshot e change report.

## Execução e docs
`python -m src.icm`, `docs/icm.md`, testes e idempotência.
