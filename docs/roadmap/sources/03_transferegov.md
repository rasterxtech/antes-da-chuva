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

# Prompt — Transferegov

## Objetivo
Implementar instrumentos e fluxos financeiros federais sem achatar o modelo relacional. Pergunta: **que instrumentos federais e fluxos financeiros estão registrados para este município?**

## Fontes oficiais
Portal: https://www.gov.br/transferegov/pt-br/ferramentas-gestao/dados-abertos
Ambiente atual de APIs/arquivos: https://api-publica.transferegov.gestao.gov.br/

Descobrir o mecanismo vigente; não criar dependência nova em endpoints descontinuados. A GOLD deve ser independente de transporte CSV/API.

## Recursos a investigar
Quando publicados: programas, programas-propostas, propostas, instrumentos/convênios, emendas, empenhos, desembolsos, pagamentos, histórico de situação, proponentes, metas, etapas, cronograma, justificativas e termos aditivos. Use nomes oficiais reais.

## RAW e SILVER
Preservar cada entidade separadamente, content-addressed. Criar tabelas SILVER relacionais: programa, proposta, instrumento, emenda, empenho, desembolso, pagamento, proponente, meta, etapa etc. Não criar mega join explosivo.

## Territorialidade
Use código IBGE quando existir. Quando não existir, investigue identificadores oficiais. Nunca associe beneficiário apenas por texto do objeto. Matching textual é apenas auxiliar e auditável.

## GOLDs
1. `fact_federal_transfer_instrument`: 1 linha por instrumento, com IDs, código IBGE, tipo/status, datas, valores distintos (global, federal, contrapartida, liberado, pago), objeto, programa, órgão, release e linhagem.
2. `fact_federal_transfer_payment`: 1 linha por pagamento, ligado ao instrumento.
3. `federal_transfer_disaster_classification`: classificação DERIVADA `PREVENTION`, `RESPONSE`, `RECONSTRUCTION`, `OTHER_RELATED`, `NOT_CLASSIFIED`, registrando regra/evidência/versão.
4. `snapshot_municipality_federal_transfer`: `codigo_ibge + reference_year`, separando contagens e valores assinados/liberados/pagos por classe.

## Classificação
Prioridade: programa/ação oficial → finalidade estruturada → órgão → outros campos estruturados → objeto → keywords. Configuração versionada em `config/transferegov_disaster_classification.json`. Determinística; não usar LLM em runtime.

## Semântica
Ausência no Transferegov não significa ausência total de investimento público. Não misturar contratado, empenhado, liberado e pago.

## DQ e atualização
Validar PKs, integridade entre entidades, chaves órfãs, datas, valores, duplicidades e cobertura. Checagem diária; preservar possibilidade de rebuild completo.

## Execução e docs
`python -m src.transferegov`, `docs/transferegov.md`, testes de ingestão relacional, mudança de transporte e idempotência.
