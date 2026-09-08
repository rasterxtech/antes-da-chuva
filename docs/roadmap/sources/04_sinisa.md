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

# Prompt — SINISA

## Objetivo
Implementar o SINISA anual. Pergunta prioritária: **que infraestrutura e gestão de drenagem/águas pluviais foram informadas oficialmente?** Preservar também os demais módulos.

## Fonte oficial
https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa

Descobrir releases, planilhas e documentação atuais.

## Módulos
Investigar Gestão Municipal, Abastecimento de Água, Esgotamento Sanitário, Resíduos Sólidos e Águas Pluviais. O foco GOLD é Águas Pluviais, mas RAW/SILVER não deve descartar os outros.

## Temporalidade
Separar `sinisa_release`, `publication_year` e `reference_year`. Nunca confundir publicação com referência.

## RAW
Preservar informações, indicadores, glossários, dicionários, atestados e documentação por release.

## Dicionário e SILVER
Criar `dim_sinisa_indicator`: `release + module + variable_or_indicator_code`, com nome, definição e unidade. Criar `silver_sinisa_value`: `release + module + codigo_ibge + variable_or_indicator_code`, preservando referência, valor, unidade e `reporting_status`. Se houver prestador/subgranularidade, preservar antes de consolidar.

Statuses: `REPORTED`, `PARTIAL`, `NOT_REPORTED`, `NOT_APPLICABLE`, `UNKNOWN`. Ausência nunca vira zero.

## GOLDs
1. `fact_municipality_sinisa_indicator`: `codigo_ibge + reference_year + module + indicator_code`.
2. `snapshot_municipality_stormwater`: `codigo_ibge + reference_year`, somente com indicadores de Águas Pluviais cuja semântica esteja comprovada pelo glossário. Investigar drenagem, rede/infraestrutura, planejamento, investimentos, despesas, manutenção, dispositivos, gestão, mapeamento e ocorrências reportadas. Não hardcode nomes antes de inspecionar o release.

## Matching e DQ
Use código IBGE quando disponível; se houver códigos próprios, mapping explícito. Validar release/reference_year, módulos, códigos, unidades, missing, status, duplicidades, cobertura e mudança de schema.

## Atualização
Checagem mensal. Novo release = preservar antigo, ingerir glossários, comparar schema, reconstruir GOLD e gerar change report.

## Execução e docs
`python -m src.sinisa`, `docs/sinisa.md`, testes e idempotência.
