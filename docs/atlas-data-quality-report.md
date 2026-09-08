# Atlas/S2ID Data Quality Report

- Status: **PASS**
- Gerado em: `2026-09-03T12:06:37+00:00`
- Release: `atlas_1991_2025_v1.1_2026-08-06`
- Data oficial da release: `2026-08-06`
- Eventos RAW/SILVER/FACT: **76190 / 76190 / 76190**
- Tipos COBRADE: **65**
- Snapshots municipais: **5571**

## Matching Municipal

- Municipios distintos na fonte: **5256**
- Municipios associados: **5256**
- Fonte sem correspondencia: **0**
- Cobertura da `dim_municipality`: **94.345719%**
- Dimensao sem registro Atlas: **315**

Ausencia de registro significa somente **0 eventos encontrados na fonte**; nao
significa que nenhum desastre ocorreu.

## Validacoes

| Regra | Status | Observado | Esperado |
|---|---:|---|---|
| `raw_resources_are_nonempty_and_readable` | PASS | `{"bytes": {"csv": 86134318, "xlsx": 71471620, "manual": 6927029, "correction_log": 158903}, "csv_rows": 76190}` | `"all resource sizes and CSV row count > 0"` |
| `csv_and_workbook_event_sets_reconcile` | PASS | `{"original_rows": 76190, "corrected_rows": 76190, "csv_ids_missing_from_original": 0, "original_ids_missing_from_csv": 0, "csv_ids_missing_from_corrected": 0, "corrected_ids_missing_from_csv": 0, "corrected_rows_with_value_differences": 0}` | `{"original_rows": 76190, "corrected_rows": 76190, "csv_ids_missing_from_original": 0, "original_ids_missing_from_csv": 0, "csv_ids_missing_from_corrected": 0, "corrected_ids_missing_from_csv": 0, "corrected_rows_with_value_differences": 0}` |
| `event_dates_match_declared_release_and_derived_fields` | PASS | `{"first_year": 1991, "latest_year": 2025, "event_year_differences": 0, "event_month_differences": 0, "invalid_months": 0}` | `{"first_year": 1991, "latest_year": 2025, "event_year_differences": 0, "event_month_differences": 0, "invalid_months": 0}` |
| `silver_required_fields_are_present` | PASS | `{"source_event_id": 0, "codigo_ibge": 0, "event_date": 0, "registration_date": 0, "cobrade_code": 0, "status_source": 0}` | `{"source_event_id": 0, "codigo_ibge": 0, "event_date": 0, "registration_date": 0, "cobrade_code": 0, "status_source": 0}` |
| `source_event_id_is_unique` | PASS | `0` | `0` |
| `territorial_and_cobrade_codes_have_valid_shapes` | PASS | `{"codigo_ibge": 0, "cobrade_code": 0}` | `{"codigo_ibge": 0, "cobrade_code": 0}` |
| `counts_and_monetary_values_are_nonnegative` | PASS | `{"columns_with_negative_values": {}}` | `{"columns_with_negative_values": {}}` |
| `human_impact_totals_reconcile` | PASS | `0` | `0` |
| `monetary_component_totals_reconcile_with_rounding_tolerance` | PASS | `{"material": 0, "public": 0, "private": 0, "public_plus_private": 0}` | `{"material": 0, "public": 0, "private": 0, "public_plus_private": 0}` |
| `cobrade_codes_and_classification_match_official_dimension` | PASS | `{"missing_codes": 0, "mapping_conflicts": 0}` | `{"missing_codes": 0, "mapping_conflicts": 0}` |
| `igp_di_correction_reference_is_consistent` | PASS | `{"nonzero_pre_real_factors": 0, "invalid_2025_reference_rows": 0}` | `{"nonzero_pre_real_factors": 0, "invalid_2025_reference_rows": 0}` |
| `source_municipalities_match_dim_municipality_by_code` | PASS | `{"source": 5256, "matched": 5256, "unmatched": 0}` | `{"source": 5256, "matched": 5256, "unmatched": 0}` |
| `raw_silver_fact_rows_and_fact_grain_reconcile` | PASS | `{"raw": 76190, "silver": 76190, "fact": 76190, "fact_duplicate_keys": 0}` | `{"raw": 76190, "silver": 76190, "fact": 76190, "fact_duplicate_keys": 0}` |
| `gold_grains_and_event_counts_reconcile` | PASS | `{"snapshot_rows": 5571, "month_profile_rows": 66852, "duplicate_keys": {"snapshot": 0, "type_summary": 0, "month_profile": 0}, "event_count_sums": {"snapshot": 76190, "type_summary": 76190, "month_profile": 76190}}` | `{"snapshot_rows": 5571, "month_profile_rows": 66852, "all_duplicate_keys": 0, "snapshot_and_month_event_count_sums": 76190, "type_summary_event_count_sum": 76190}` |
| `recognition_status_values_are_known` | PASS | `{"Reconhecido": 35608, "Registro": 40582}` | `"only Registro and Reconhecido"` |

## Problemas Encontrados

Nenhum problema de qualidade encontrado.

## Ressalvas

- Anomalias de protocolo, data, chave natural e nomes territoriais da fonte foram preservadas e quantificadas; nenhum ID foi reescrito.
- 315 unidades da dim_municipality nao possuem registro Atlas; isso significa 0 eventos encontrados na fonte.
- A dimensao oficial contem codigos COBRADE sem eventos nesta release: 11200, 15140, 21310, 22450, 25400.

## Anomalias Preservadas

```json
{
  "invalid_protocol_format": 7,
  "protocol_ibge_conflicts": 4,
  "protocol_cobrade_conflicts": 325,
  "event_after_registration": 12,
  "natural_key_duplicate_groups": 78,
  "municipality_codes_with_name_variants": 51
}
```

Os dados descrevem registros oficiais historicos. Nao representam risco futuro,
probabilidade de desastre, causalidade ou ausencia do fenomeno.
