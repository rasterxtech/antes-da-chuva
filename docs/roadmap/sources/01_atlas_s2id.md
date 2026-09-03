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

# Prompt — Atlas Digital de Desastres / S2ID

## Objetivo
Implementar a fonte oficial de histórico de desastres para responder **o que já aconteceu neste município segundo os registros oficiais**, sem inferir risco futuro.

## Fonte oficial
Página canônica de descoberta: https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml

Descobrir a cada execução os recursos vigentes. Priorizar e preservar, quando disponíveis: Base Completa CSV, Base Completa XLSX, Manual de Tratamento, Log de Correções e documentação metodológica vinculada. Não dependa de URL final fixa.

## Descoberta e atualização
Fluxo: página oficial → descobrir arquivos → obter metadata HTTP → comparar com manifest → baixar se necessário → preservar RAW → reprocessar se hash/release mudou. Mudança no log de correções deve ser registrada.

## RAW
`data/raw/atlas/discovery/` e `data/raw/atlas/<release_or_snapshot>/files/`. Preservar arquivos sem transformação.

## Inspeção obrigatória
Inspecionar schema real, tipos, encoding, datas, IDs, COBRADE, danos humanos, danos monetários, reconhecimento federal, duplicidades e diferenças entre releases. Não presumir nomes de colunas.

## SILVER
Criar `silver_disaster_event`, grão **1 linha por registro/evento oficial**. Preservar quando existirem: `source_event_id`, `codigo_ibge`, nomes territoriais originais, `event_date`, ano/mês, `cobrade_code`, descrição/hierarquia, tipo, mortos, feridos, enfermos, desabrigados, desalojados, desaparecidos, afetados, danos públicos/privados, reconhecimento, release, hash e ingestão.

Criar `dim_disaster_type`, 1 linha por COBRADE, com código, nome, grupo, subgrupo, hierarquia e release. Preferir COBRADE a keywords.

## Classificação derivada
A fact preserva todos os desastres. Criar flags versionadas `is_rain_related`, `is_hydrological`, `is_geological`, baseadas preferencialmente na classificação oficial. Incluir quando aplicável inundação, enxurrada, alagamento, chuvas intensas e movimentos de massa associados à chuva.

## GOLDs
1. `fact_disaster_event`: `codigo_ibge + disaster_event_id`.
2. `snapshot_municipality_disaster_history`: `codigo_ibge + reference_date`, com primeiro/último evento, total, eventos relacionados à chuva, janelas 5/10/20 anos, mortos, feridos, desabrigados, desalojados e afetados.
3. `municipality_disaster_type_summary`: `codigo_ibge + cobrade_code`, com contagem, primeiro/último evento e impactos.
4. `municipality_disaster_month_profile`: `codigo_ibge + month`, com contagem total e relacionada à chuva. Sazonalidade histórica não é probabilidade.

## Matching territorial e DQ
Validar contra `dim_municipality`; reportar source/matched/unmatched/dim_without_record/coverage. Sem registro = “0 eventos encontrados na fonte”, nunca “nenhum desastre ocorreu”. Validar chaves, datas, COBRADE, valores não negativos, duplicidades, cobertura e reconciliação RAW→SILVER→GOLD.

## Execução e docs
Criar `python -m src.atlas`, `docs/atlas.md`, testes de discovery/schema/matching/idempotência. Concluir somente após segunda execução `NO_CHANGE`.
