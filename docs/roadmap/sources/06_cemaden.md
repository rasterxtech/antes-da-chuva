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

# Prompt — Cemaden

## Objetivo
Implementar três subprodutos independentes: municípios monitorados, inventário de estações e observações públicas automatizáveis.

## Fontes oficiais
Portal: https://www.gov.br/cemaden/
Mapa: https://mapainterativo.cemaden.gov.br/

Descobrir páginas/endpoints oficiais. Não contornar CAPTCHA, autenticação, desafio anti-bot nem usar OCR para CAPTCHA. Se um subproduto depender de interação humana sem endpoint oficial equivalente, marcar `BLOCKED_SOURCE` e documentar ingestão manual futura.

## A. Municípios monitorados
Criar `snapshot_cemaden_monitored_municipality`: `codigo_ibge + snapshot_date`, com `is_monitored`, `monitoring_since`, `monitoring_type` quando disponíveis. Não hardcode número atual.

## B. Estações
Criar `dim_cemaden_station`: 1 linha por estação/equipamento, com `station_id`, tipo, código IBGE, nome territorial original, latitude, longitude, elevação, instalação, status e linhagem. Não forçar mesmo schema para todos os tipos.

## C. Observações
Quando houver acesso público automatizável, criar facts separadas, ex.: `fact_cemaden_rainfall_observation` e `fact_cemaden_hydrological_observation`, grão `station_id + observed_at_utc`. Não misturar chuva, nível de rio e geotecnia. Preservar UTC original.

## Qualidade observacional
Dados brutos podem ter inconsistências. Não corrigir silenciosamente; adicionar `quality_status`/`quality_issue` quando suportado.

## GOLD municipal
Criar `snapshot_municipality_cemaden_monitoring`: `codigo_ibge + snapshot_date`, com contagens por tipo de estação.

Se observações estiverem estáveis, podem existir métricas descritivas de chuva diária, máximo diário e dias acima de thresholds explícitos. Não chamar thresholds de risco e não criar previsão.

## Matching e DQ
Prefira município informado pela fonte. Spatial matching só quando necessário e documentado. Validar IDs, coordenadas, códigos, timestamps, valores físicos, duplicidades, cobertura e mudança de inventário.

## Atualização
Municípios/inventário: diária. Observações: conforme viabilidade oficial.

## Execução e docs
`python -m src.cemaden` (opcionalmente subcomandos), `docs/cemaden.md`, testes. Concluir mesmo se observações ficarem `BLOCKED_SOURCE`, desde que isso esteja explícito e o restante esteja `PASS`.
