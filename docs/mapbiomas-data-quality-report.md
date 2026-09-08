# MapBiomas Data Quality Report

- Status: **PASS**
- Gerado em: `2026-09-02T21:05:32+00:00`
- Colecao: `11`
- Versao: `v1`
- Publicacao: `2026-08-12`
- Serie: `1985–2025`
- RAW: **77406** linhas largas
- SILVER: **3173605** linhas
- FACT: **2798168** linhas
- SNAPSHOT: **228370** linhas
- CHANGE: **5570** linhas

## Matching Municipal

- MapBiomas: **5572** codigos
- `dim_municipality`: **5571** codigos
- Matched: **5570**
- Cobertura da dimensao: **99.982050%**
- MapBiomas sem dimensao: `['4300001', '4300002']`
- Dimensao sem MapBiomas: `['2605459']`

## Classes dos Indicadores

- Area urbanizada: `24`
- Agua: `33`
- Campo alagado/area pantanosa: `11`
- Vegetacao nativa: `(3, 4, 5, 6, 7, 11, 12, 13, 29, 32, 49, 50, 84)`
- Agropecuaria: `(9, 15, 20, 21, 35, 39, 40, 41, 46, 47, 48, 62)`
- Classes mapeadas no denominador: `(3, 4, 5, 6, 7, 9, 11, 12, 13, 15, 20, 21, 23, 24, 25, 29, 30, 31, 32, 33, 35, 39, 40, 41, 46, 47, 48, 49, 50, 62, 75, 84, 91)`
- Classes excluidas como nao observadas: `(0,)`

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
| `raw_files_are_nonempty_and_readable` | PASS | `{"statistics_bytes": 78296450, "legend_bytes": 1521, "xlsx_rows": 77406}` | `{"statistics_bytes": "> 0", "legend_bytes": "> 0", "xlsx_rows": "> 0"}` |
| `annual_series_is_complete` | PASS | `{"min_year": 1985, "max_year": 2025, "year_count": 41, "gaps": []}` | `{"min_year": 1985, "max_year": 2025, "year_count": 41, "gaps": []}` |
| `silver_required_fields_and_nonnegative_area` | PASS | `{"nulls": {"collection_id": 0, "collection_version": 0, "codigo_ibge": 0, "biome_name": 0, "year": 0, "class_id": 0, "class_name": 0, "class_level": 0, "area_ha": 0}, "negative_area_rows": 0}` | `{"nulls": {"collection_id": 0, "collection_version": 0, "codigo_ibge": 0, "biome_name": 0, "year": 0, "class_id": 0, "class_name": 0, "class_level": 0, "area_ha": 0}, "negative_area_rows": 0}` |
| `silver_grain_is_unique_and_reconciled` | PASS | `{"rows": 3173605, "duplicate_keys": 0}` | `{"rows": 3173605, "duplicate_keys": 0}` |
| `municipality_dimension_coverage` | PASS | `{"municipios_mapbiomas": 5572, "municipios_dim_municipality": 5571, "municipios_matched": 5570, "municipios_unmatched": 2, "codigo_mapbiomas_sem_dim": ["4300001", "4300002"], "codigo_dim_sem_mapbiomas": ["2605459"], "coverage_pct": 99.98204990127446}` | `{"coverage_pct": ">= 99.0"}` |
| `fact_grain_and_biome_sum_are_correct` | PASS | `{"duplicate_keys": 0, "aggregation_differences": 0}` | `{"duplicate_keys": 0, "aggregation_differences": 0}` |
| `indicator_classes_come_from_official_hierarchy` | PASS | `{"urban": 24, "water": 33, "wetland": 11, "native_vegetation": [3, 4, 5, 6, 7, 11, 12, 13, 29, 32, 49, 50, 84], "agriculture_livestock": [9, 15, 20, 21, 35, 39, 40, 41, 46, 47, 48, 62]}` | `"all IDs present in the official statistics hierarchy"` |
| `mapped_municipality_area_is_positive_and_stable` | PASS | `{"nonpositive_rows": 0, "over_warning_threshold": 1, "over_failure_threshold": 0, "max_variation_pct": 0.13344768719492786, "variation_quantiles_pct": {"p50": 8.553470781323938e-12, "p90": 4.6473080545672487e-11, "p95": 3.3842308079619807e-10, "p99": 0.0036651461629546023}}` | `{"nonpositive_rows": 0, "over_failure_threshold": 0, "failure_threshold_pct": 1.0}` |
| `snapshot_percentages_are_bounded` | PASS | `{"urban_area_pct": 0, "native_vegetation_area_pct": 0, "agriculture_livestock_area_pct": 0, "water_area_pct": 0, "wetland_area_pct": 0}` | `{"urban_area_pct": 0, "native_vegetation_area_pct": 0, "agriculture_livestock_area_pct": 0, "water_area_pct": 0, "wetland_area_pct": 0}` |
| `required_municipality_examples_are_present` | PASS | `4` | `4` |

## Problemas Encontrados

Nenhum problema de qualidade encontrado.

## Ressalvas

- O XLSX e o CSV oficial de legenda possuem conjuntos de classes diferentes; classes exclusivas do XLSX usam a hierarquia do workbook.
- A cobertura municipal nao e exatamente igual a dim_municipality; os codigos divergentes permanecem explicitos no matching report.
- A fonte possui grao duplicado; a SILVER consolida por soma e preserva source_row_count e as listas de estados/regioes originais.
- 1 municipio(s) excedem 0.1% de variacao da area mapeada entre anos, sem exceder o limite de falha.

## Exemplos no Ultimo Ano

| codigo_ibge | municipio | primeiro ano | ultimo ano | urbano ha | urbano % | vegetacao nativa ha | vegetacao nativa % | agua ha | area umida ha | mudanca urbana ha | mudanca vegetacao ha |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3304557 | Rio de Janeiro | 1985 | 2025 | 58755.377 | 49.129 | 37297.174 | 31.187 | 2321.324 | 5273.899 | 17029.352 | 2620.541 |
| 3550308 | São Paulo | 1985 | 2025 | 89724.834 | 58.985 | 41196.860 | 27.083 | 5823.928 | 1148.441 | 13665.699 | -6615.051 |
| 4202404 | Blumenau | 1985 | 2025 | 8166.298 | 15.747 | 35728.911 | 68.896 | 557.580 | 0.000 | 4845.927 | -3.961 |
| 5300108 | Brasília | 1985 | 2025 | 72030.460 | 12.503 | 272539.156 | 47.308 | 6579.822 | 3626.217 | 40241.887 | -112336.617 |

Os indicadores descrevem cobertura observada. Nao representam risco, causalidade,
impermeabilizacao, disponibilidade hidrica ou vulnerabilidade.
