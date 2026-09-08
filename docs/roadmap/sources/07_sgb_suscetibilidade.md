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

# Prompt — SGB: Cartografia de Suscetibilidade

## Objetivo
Implementar a Cartografia de Suscetibilidade do Serviço Geológico do Brasil. Pergunta: **que suscetibilidade foi oficialmente mapeada no território deste município?** `suscetibilidade != risco`.

## Fonte oficial
https://www.sgb.gov.br/produtos-por-estado-cartografia-de-suscetibilidade

Descobrir a cobertura vigente; não hardcode quantidade. Implementar crawler restrito ao domínio oficial do SGB, seguindo estado → município → produto.

## Descoberta/RAW
Descobrir município, UF, código quando disponível, produto, escala, data, arquivos e metadados. Preservar vetores, PDFs, notas e documentação. Priorizar vetor para processamento.

## Spatial
Pode usar extensão oficial DuckDB Spatial. Não adicionar GeoPandas apenas por conveniência.

## SILVER
Criar `silver_sgb_susceptibility_polygon`: 1 linha por feature/polígono, com `codigo_ibge`, tipo de suscetibilidade, classe, geometria, arquivo, escala, data, hash e ingestão. Descobrir nomes/classes reais; não presumir.

## GOLDs
1. `fact_municipality_susceptibility_area`: `codigo_ibge + susceptibility_type + susceptibility_class`, com área km², área municipal, percentual, data do produto e linhagem. Documentar CRS/método de área.
2. `snapshot_municipality_sgb_coverage`: `codigo_ibge + snapshot_date`, com `has_susceptibility_mapping`, `product_count`, `latest_product_date`, `available_types`. Ausência de cobertura não significa ausência de suscetibilidade.

## Geometria
Validar `ST_IsValid`. Não corrigir silenciosamente. Qualquer repair deve ser explícito, rastreável e separado da geometria original.

## Territorialidade
Use associação oficial a município quando disponível. Depois metadado/nome+UF auditável; interseção espacial somente em último caso.

## DQ e atualização
Validar geometrias, áreas > 0, classes, município, duplicidades, sobreposições inesperadas, escala e arquivos faltantes. Checagem mensal; novos produtos não apagam antigos.

## Execução e docs
`python -m src.sgb`, `docs/sgb.md`, testes e idempotência.
