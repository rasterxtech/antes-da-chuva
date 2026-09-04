# MUNIC 2020 Data Quality Report

- Status: **PASS**
- Gerado em: `2026-09-04T01:26:35+00:00`
- SILVER: **5570** linhas
- GOLD: **5571** linhas
- Fora da fonte de 2020: `['5101837']`

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
| `source_has_5570_municipalities` | PASS | `5570` | `5570` |
| `source_codigo_ibge_is_unique` | PASS | `0` | `0` |
| `source_codigo_ibge_format_is_valid` | PASS | `0` | `0` |
| `all_source_codes_match_current_dimension` | PASS | `0` | `0` |
| `gold_matches_current_dimension` | PASS | `5571` | `5571` |
| `new_municipality_is_explicitly_outside_2020_source` | PASS | `["5101837"]` | `["5101837"]` |
| `status_values_follow_contract` | PASS | `{}` | `{}` |
| `budget_not_applicable_is_not_used_for_declared_compdec` | PASS | `0` | `0` |
| `selected_indicator_counts_match_2020_release` | PASS | `{"municipal_civil_defense_body_status": 4236, "flood_risk_mapping_status": 2164, "flood_contingency_plan_status": 1407, "flood_early_warning_status": 436, "landslide_contingency_plan_status": 1016, "landslide_early_warning_status": 246, "civil_defense_budget_provision_status": 968, "civil_defense_early_warning_status": 435}` | `{"municipal_civil_defense_body_status": 4236, "flood_risk_mapping_status": 2164, "flood_contingency_plan_status": 1407, "flood_early_warning_status": 436, "landslide_contingency_plan_status": 1016, "landslide_early_warning_status": 246, "civil_defense_budget_provision_status": 968, "civil_defense_early_warning_status": 435}` |

## Contagens declaradas como Sim

| Indicador | Municipios |
|---|---:|
| `municipal_civil_defense_body_status` | 4236 |
| `flood_risk_mapping_status` | 2164 |
| `flood_contingency_plan_status` | 1407 |
| `flood_early_warning_status` | 436 |
| `landslide_contingency_plan_status` | 1016 |
| `landslide_early_warning_status` | 246 |
| `civil_defense_budget_provision_status` | 968 |
| `civil_defense_early_warning_status` | 435 |

## Ressalvas

- As respostas foram declaradas pelas prefeituras e se referem a 2020.
- Recusa, nao informou, nao sabe e nao se aplica permanecem estados distintos.
- A variavel Mgrd201 usa o significado do questionario oficial: mapeamento de risco em encostas; o dicionario repete por engano o rotulo de inundacoes.
- Previsao orcamentaria e recursos da COMPDEC sao quesitos condicionais; nao se aplica nunca equivale a nao.
