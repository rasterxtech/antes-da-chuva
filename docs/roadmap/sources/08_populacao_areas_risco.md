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

# Prompt — IBGE/Cemaden: População em Áreas de Risco

## Objetivo
Implementar o estudo oficial preservando releases, referência censitária e universo de áreas mapeadas. Pergunta: **quantas pessoas e domicílios estão associados às áreas de risco incluídas no estudo oficial?** Não afirmar que o estudo representa toda a população em risco do município.

## Fontes oficiais
Produto principal: https://www.ibge.gov.br/geociencias/informacoes-ambientais/estudos-ambientais/21538-populacao-em-areas-de-risco-no-brasil.html
Monitor de novos produtos: https://www.ibge.gov.br/singedlab-desastres/

Detectar releases novos quando publicados.

## Versionamento
Preservar `release_id`, `census_reference_year`, `risk_geometry_reference`. Nunca sobrescrever edição anterior.

## RAW
Preservar tabelas de população/domicílios, shapefiles/geometrias, notas, dicionários, documentação e páginas de descoberta.

## SILVER
1. `silver_risk_area_population`: preservar unidade espacial original (setor/BATER/área/etc.) e variáveis.
2. `silver_risk_area_household`: mesmo princípio.
Preservar identificadores espaciais e tipos de risco em dimensões auxiliares quando existirem. Não reduzir imediatamente a município.

## GOLD
Criar `snapshot_municipality_risk_population`: `codigo_ibge + census_reference_year + release_id`, com indicadores diretamente suportados, como população/domicílios em áreas mapeadas, população municipal de referência, percentual e recortes demográficos documentados.

Criar `risk_mapping_coverage_status` e, quando possível, contagem/referência das áreas mapeadas.

## Nova edição
Ao detectar novo release: preservar anterior, comparar schema, referência censitária, cobertura e metodologia. Criar `risk_population_release_comparison.json` com releases, census years, mudanças de schema/cobertura e `methodology_comparable`. Não calcular automaticamente variação se não for comparável.

## Spatial
Se necessário ler SHP, usar DuckDB Spatial e preservar geometria original.

## DQ
Validar IDs, código IBGE, população/domicílios >=0, percentuais, cobertura, duplicidade, agregação e reconciliação com totais publicados quando possível.

## Atualização
Checagem mensal; normalmente `NO_CHANGE`.

## Execução e docs
`python -m src.risk_population`, `docs/risk-population.md`, testes e idempotência.
