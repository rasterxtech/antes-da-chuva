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

# Prompt — MIDR: Municípios Prioritários / Cadastro Nacional

## Objetivo
Implementar a indicação/priorização federal e distinguir isso de inscrição formal no Cadastro Nacional.

## Fonte oficial
https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/cadastro-nacional-de-municipios

Descobrir lista vigente, notas técnicas, critérios, datas e informações de cadastro.

## Regra semântica
`Indicação da União != inscrição no Cadastro Nacional`. Também `não indicado != sem risco`.

## RAW e SILVER
Preservar página, lista, notas, PDFs e anexos. Criar `silver_midr_priority_municipality`: `snapshot/release + codigo_ibge`, com `is_union_indicated`, `is_national_registry_enrolled`, `registry_status`, referência metodológica e linhagem. Se inscrição não estiver pública/estruturada, não inferir: use NULL/UNKNOWN.

## GOLDs
1. `snapshot_municipality_federal_priority`: `codigo_ibge + snapshot_date`, com indicação, cadastro/status, versão, metodologia e publicação.
2. `municipality_federal_priority_change`: código, snapshot anterior/atual e `ADDED|REMOVED|UNCHANGED`. `REMOVED` não significa risco reduzido.

## Matching e DQ
Prefira código IBGE. Se só houver nome/UF, matching determinístico e auditável. Validar unicidade, total descoberto na fonte, cobertura, duplicidades e versão. Não hardcode quantidade esperada.

## Atualização
Checagem semanal. Sem mudança = `NO_CHANGE`; nova lista = preservar anterior + snapshot + change table.

## Execução e docs
`python -m src.midr`, `docs/midr-priority.md`, testes e idempotência.
