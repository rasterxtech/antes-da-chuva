# Data Quality Report

- Status: **PASS**
- Gerado em: `2026-09-03T12:06:12+00:00`
- Consulta da fonte: `2026-09-03`
- Registros oficiais retornados pela API: **5571**
- Localidades no nivel municipal em `dim_municipality`: **5571**
- Municipios stricto sensu: **5569**
- UFs: **27**
- Regioes: **5**
- Duplicados de `codigo_ibge`: **0**
- Tipos territoriais: `distrito_estadual`: 1, `distrito_federal`: 1, `municipio`: 5569

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
| `record_count_matches_official_api_response` | PASS | `5571` | `5571` |
| `codigo_ibge_is_unique` | PASS | `0` | `0` |
| `required_fields_are_not_null` | PASS | `{"codigo_ibge": 0, "municipio": 0, "sigla_uf": 0, "codigo_uf_ibge": 0, "regiao": 0}` | `{"codigo_ibge": 0, "municipio": 0, "sigla_uf": 0, "codigo_uf_ibge": 0, "regiao": 0}` |
| `codigo_ibge_set_matches_official_api_response` | PASS | `{"missing_count": 0, "unexpected_count": 0}` | `{"missing_count": 0, "unexpected_count": 0}` |
| `administrative_code_formats_are_valid` | PASS | `{"invalid_codigo_ibge": 0, "invalid_codigo_uf_ibge": 0, "invalid_codigo_regiao": 0, "invalid_codigo_regiao_imediata": 0, "invalid_codigo_regiao_intermediaria": 0, "municipality_uf_prefix_conflicts": 0}` | `{"invalid_codigo_ibge": 0, "invalid_codigo_uf_ibge": 0, "invalid_codigo_regiao": 0, "invalid_codigo_regiao_imediata": 0, "invalid_codigo_regiao_intermediaria": 0, "municipality_uf_prefix_conflicts": 0}` |
| `each_municipality_belongs_to_exactly_one_uf` | PASS | `0` | `0` |
| `each_uf_belongs_to_exactly_one_region` | PASS | `0` | `0` |
| `current_geographic_regions_are_complete` | PASS | `{"regiao_imediata": 0, "codigo_regiao_imediata": 0, "regiao_intermediaria": 0, "codigo_regiao_intermediaria": 0}` | `{"regiao_imediata": 0, "codigo_regiao_imediata": 0, "regiao_intermediaria": 0, "codigo_regiao_intermediaria": 0}` |
| `required_documentation_examples_are_present` | PASS | `5` | `5` |
| `special_territorial_units_are_classified` | PASS | `0` | `0` |

## Nulls

| Coluna | Nulls |
|---|---:|
| `codigo_ibge` | 0 |
| `municipio` | 0 |
| `municipio_normalized` | 0 |
| `uf` | 0 |
| `sigla_uf` | 0 |
| `codigo_uf_ibge` | 0 |
| `regiao` | 0 |
| `codigo_regiao` | 0 |
| `regiao_imediata` | 0 |
| `codigo_regiao_imediata` | 0 |
| `regiao_intermediaria` | 0 |
| `codigo_regiao_intermediaria` | 0 |
| `tipo_unidade_territorial` | 0 |
| `source` | 0 |
| `source_url` | 0 |
| `source_updated_at` | 5571 |
| `ingested_at` | 0 |

`source_updated_at` nulo e esperado: a API nao fornece essa metadata.

## Problemas Encontrados

Nenhum problema de qualidade encontrado.

## Ressalvas

- source_updated_at esta nulo porque a API nao informa versao, data de referencia, Last-Modified ou ETag.
- A rota de municipios inclui Brasilia (Distrito Federal) e Fernando de Noronha (distrito estadual) no nivel analitico municipal.
- Mesorregiao e microrregiao foram mantidas apenas na SILVER; a microrregiao e nula para Boa Esperanca do Norte na fonte atual.

## Exemplos

| codigo_ibge | municipio | UF | regiao | regiao_imediata | regiao_intermediaria |
|---|---|---|---|---|---|
| 2605459 | Fernando de Noronha | PE | Nordeste | Recife | Recife |
| 3304557 | Rio de Janeiro | RJ | Sudeste | Rio de Janeiro | Rio de Janeiro |
| 3550308 | São Paulo | SP | Sudeste | São Paulo | São Paulo |
| 4202404 | Blumenau | SC | Sul | Blumenau | Blumenau |
| 5300108 | Brasília | DF | Centro-Oeste | Distrito Federal | Distrito Federal |

O relatorio estruturado esta em `data/gold/data_quality_report.json`.
