# Atlas Digital de Desastres / S2ID

## Fonte e Release

- Fonte oficial: Atlas Digital de Desastres no Brasil / S2ID.
- Descoberta canonica: `https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml`.
- Release: `atlas_1991_2025_v1.1_2026-08-06`.
- Data oficial identificada no nome do arquivo: `2026-08-06`.
- Serie declarada: `1991`–`2025`.
- Modo de descoberta: `automatic`.
- CSV: `https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv`.
- XLSX: `https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx`.
- Manual: `https://atlasdigital.mdr.gov.br/arquivos/Atlas_Digital_Desastres_Manual_Aplicacao.pdf`.
- Log de correcoes: `https://atlasdigital.mdr.gov.br/arquivos/2026/2026.08-logs-correcoes.xlsx`.

O pipeline redescobre os quatro recursos na pagina oficial. URLs finais nao sao
fixadas no codigo. Overrides `ATLAS_CSV_URL`, `ATLAS_XLSX_URL`,
`ATLAS_MANUAL_URL` e `ATLAS_LOG_URL` existem apenas para recuperacao operacional
e ficam registrados no RAW.

## Execucao

```bash
python -m src.atlas
```

Uma assinatura combina release, URLs oficiais, hashes dos quatro recursos e o
fingerprint do pipeline. Se nada mudou e todos os artefatos existem, a execucao
termina em `NO_CHANGE` sem reconstruir os Parquets. Uma nova release preserva o
RAW anterior, arquiva as GOLDs e gera um relatorio de impacto.

## Inspecao da Fonte

- CSV `CP1252`, delimitador `;`, aspas
  `"` e fim de linha `LF`.
- **76190** registros logicos e **210997**
  linhas fisicas; narrativas entre aspas podem conter quebras de linha.
- **70** colunas validadas em ordem exata.
- Eventos: `1991-01-07` a `2025-12-31`.
- Registros: `1991-01-07` a
  `2026-03-24`.
- **5256** codigos municipais observados.
- **60** COBRADE observados e
  **65** na dimensao oficial do workbook.
- Valores monetarios corrigidos por IGP-DI para dezembro de
  **2025**, indice
  **1167.239**.

| Coluna original | Tipo observado no XLSX |
|---|---|
| `Protocolo_S2iD` | `VARCHAR` |
| `Nome_Municipio` | `VARCHAR` |
| `Sigla_UF` | `VARCHAR` |
| `regiao` | `VARCHAR` |
| `Data_Registro` | `DATE` |
| `Data_Evento` | `DATE` |
| `Cod_Cobrade` | `DOUBLE` |
| `tipologia` | `DOUBLE` |
| `descricao_tipologia` | `VARCHAR` |
| `grupo_de_desastre` | `VARCHAR` |
| `Cod_IBGE_Mun` | `DOUBLE` |
| `Setores Censitários` | `VARCHAR` |
| `Status` | `VARCHAR` |
| `DH_Descricao` | `VARCHAR` |
| `DH_MORTOS` | `DOUBLE` |
| `DH_FERIDOS` | `DOUBLE` |
| `DH_ENFERMOS` | `DOUBLE` |
| `DH_DESABRIGADOS` | `DOUBLE` |
| `DH_DESALOJADOS` | `DOUBLE` |
| `DH_DESAPARECIDOS` | `DOUBLE` |
| `DH_AFETADOS_SECA_ESTIAGEM` | `DOUBLE` |
| `DH_total_danos_humanos_diretos` | `DOUBLE` |
| `DH_OUTROS AFETADOS` | `DOUBLE` |
| `DM_Descricao` | `VARCHAR` |
| `DM_Uni Habita Danificadas` | `DOUBLE` |
| `DM_Uni Habita Destruidas` | `DOUBLE` |
| `DM_Uni Habita Valor` | `DOUBLE` |
| `DM_Inst Saúde Danificadas` | `DOUBLE` |
| `DM_Inst Saúde Destruidas` | `DOUBLE` |
| `DM_Inst Saúde Valor` | `DOUBLE` |
| `DM_Inst Ensino Danificadas` | `DOUBLE` |
| `DM_Inst Ensino Destruidas` | `DOUBLE` |
| `DM_Inst Ensino Valor` | `DOUBLE` |
| `DM_Inst Serviços Danificadas` | `DOUBLE` |
| `DM_Inst Serviços Destruidas` | `DOUBLE` |
| `DM_Inst Serviços Valor` | `DOUBLE` |
| `DM_Inst Comuni Danificadas` | `DOUBLE` |
| `DM_Inst Comuni Destruidas` | `DOUBLE` |
| `DM_Inst Comuni Valor` | `DOUBLE` |
| `DM_Obras de Infra Danificadas` | `DOUBLE` |
| `DM_Obras de Infra Destruidas` | `DOUBLE` |
| `DM_Obras de Infra Valor` | `DOUBLE` |
| `DM_total_danos_materiais` | `DOUBLE` |
| `DA_Descricao` | `VARCHAR` |
| `DA_Polui/cont da água` | `DOUBLE` |
| `DA_Polui/cont do ar` | `DOUBLE` |
| `DA_Polui/cont do solo` | `DOUBLE` |
| `DA_Dimi/exauri hídrico` | `DOUBLE` |
| `DA_Incêndi parques/APA's/APP's` | `DOUBLE` |
| `PEPL_Descricao` | `VARCHAR` |
| `PEPL_Assis_méd e emergên(R$)` | `DOUBLE` |
| `PEPL_Abast de água pot(R$)` | `DOUBLE` |
| `PEPL_sist de esgotos sanit(R$)` | `DOUBLE` |
| `PEPL_Sis limp e rec lixo (R$)` | `DOUBLE` |
| `PEPL_Sis cont pragas (R$)` | `DOUBLE` |
| `PEPL_distrib energia (R$)` | `DOUBLE` |
| `PEPL_Telecomunicações (R$)` | `DOUBLE` |
| `PEPL_Tran loc/reg/l_curso (R$)` | `DOUBLE` |
| `PEPL_Distrib combustíveis(R$)` | `DOUBLE` |
| `PEPL_Segurança pública (R$)` | `DOUBLE` |
| `PEPL_Ensino (R$)` | `DOUBLE` |
| `PEPL_total_publico` | `DOUBLE` |
| `PEPR_Descricao` | `VARCHAR` |
| `PEPR_Agricultura (R$)` | `DOUBLE` |
| `PEPR_Pecuária (R$)` | `DOUBLE` |
| `PEPR_Indústria (R$)` | `DOUBLE` |
| `PEPR_Comércio (R$)` | `DOUBLE` |
| `PEPR_Serviços (R$)` | `DOUBLE` |
| `PEPR_total_privado` | `DOUBLE` |
| `PE_PLePR` | `DOUBLE` |

O CSV de valores corrigidos e a entrada canonica dos eventos. O XLSX fornece a
dimensao COBRADE, os fatores de correcao e uma reconciliacao independente. O
pipeline exige igualdade dos IDs e dos 70 valores entre o CSV e a folha `Atlas
Valores Corrigidos`. O manual e o log sao preservados integralmente e seus hashes
participam da identidade da carga.

## Granularidades

- `silver_disaster_event`: uma linha por registro oficial, inclusive divergencias.
- `dim_disaster_type` (SILVER): uma linha por COBRADE presente na folha oficial.
- `fact_disaster_event`: `codigo_ibge + disaster_event_id`.
- `snapshot_municipality_disaster_history`: `codigo_ibge + reference_date`.
- `municipality_disaster_type_summary`: `codigo_ibge + cobrade_code`.
- `municipality_disaster_month_profile`: `codigo_ibge + month`.

O snapshot e o perfil mensal incluem toda a `dim_municipality`. Um zero significa
somente **0 eventos encontrados na fonte**, nunca ausencia comprovada de desastre.
As janelas de 5, 10 e 20 anos sao intervalos retroativos estritos a partir da
ultima data de evento da release.

A FACT preserva todos os registros, inclusive eventuais codigos historicos sem
correspondencia na dimensao vigente. Snapshots e perfis municipais agregam apenas
os registros associados por `codigo_ibge`, sem fallback por nome.

## Classificacao Derivada

- `is_hydrological`: grupo COBRADE oficial de codigo `12`.
- `is_geological`: grupo COBRADE oficial de codigo `11`.
- `is_rain_related`: inundacao `12100`, enxurrada `12200`, alagamento `12300`,
  chuvas intensas `13214` e movimentos de massa `11311`–`11340` enumerados na
  versao `atlas_cobrade_rain_v1`.

As flags sao classificacoes documentais versionadas, nao inferencias causais para
um evento particular. A FACT preserva todos os tipos de desastre.

## Matching e Qualidade

- Fonte: **5256** municipios.
- Matched por `codigo_ibge`: **5256**.
- Fonte sem dimensao: **0**.
- Cobertura da dimensao: **94.345719%**.
- Dimensao sem registro: **315**.
- Protocolos fora do formato: **7**.
- Conflitos protocolo/IBGE: **4**.
- Conflitos protocolo/COBRADE: **325**.
- Evento posterior ao registro: **12**.
- Grupos duplicados na chave natural: **78**.

`Cod_IBGE_Mun`, `Cod_Cobrade`, `Data_Evento` e `Data_Registro` sao campos
canonicos da linha. O protocolo e um identificador opaco: suas partes nao
sobrescrevem os campos explicitos. Registros com a mesma chave natural e IDs
distintos nao sao deduplicados.

`direct_human_damage_total` reproduz a soma oficial de mortos, feridos, enfermos,
desabrigados, desalojados, desaparecidos e afetados por seca/estiagem.
`reported_affected_total` adiciona `other_affected`. Totais monetarios admitem
R$ 0,05 de diferenca por arredondamento dos componentes exibidos.

## Schema `dim_disaster_type`

| Nome | Tipo |
|---|---|
| `cobrade_code` | `VARCHAR` |
| `disaster_name` | `VARCHAR` |
| `atlas_type_name` | `VARCHAR` |
| `atlas_type_id` | `SMALLINT` |
| `atlas_group_name` | `VARCHAR` |
| `cobrade_category_code` | `VARCHAR` |
| `cobrade_group_code` | `VARCHAR` |
| `cobrade_subgroup_code` | `VARCHAR` |
| `is_hydrological` | `BOOLEAN` |
| `is_geological` | `BOOLEAN` |
| `is_rain_related` | `BOOLEAN` |
| `classification_version` | `VARCHAR` |
| `source_release` | `VARCHAR` |
| `source_sha256` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` |

## Schema `fact_disaster_event`

| Nome | Tipo |
|---|---|
| `disaster_event_id` | `VARCHAR` |
| `source_event_id` | `VARCHAR` |
| `codigo_ibge` | `VARCHAR` |
| `municipality_name_source` | `VARCHAR` |
| `uf_code_source` | `VARCHAR` |
| `region_name_source` | `VARCHAR` |
| `registration_date` | `DATE` |
| `event_date` | `DATE` |
| `event_year` | `SMALLINT` |
| `event_month` | `TINYINT` |
| `cobrade_code` | `VARCHAR` |
| `atlas_type_id` | `SMALLINT` |
| `atlas_type_name_source` | `VARCHAR` |
| `atlas_group_name_source` | `VARCHAR` |
| `census_sectors_source` | `VARCHAR` |
| `status_source` | `VARCHAR` |
| `is_federally_recognized` | `BOOLEAN` |
| `human_damage_description` | `VARCHAR` |
| `deaths` | `BIGINT` |
| `injured` | `BIGINT` |
| `ill` | `BIGINT` |
| `homeless` | `BIGINT` |
| `displaced` | `BIGINT` |
| `missing` | `BIGINT` |
| `drought_affected` | `BIGINT` |
| `direct_human_damage_total` | `BIGINT` |
| `other_affected` | `BIGINT` |
| `reported_affected_total` | `BIGINT` |
| `material_damage_description` | `VARCHAR` |
| `housing_units_damaged` | `BIGINT` |
| `housing_units_destroyed` | `BIGINT` |
| `housing_damage_brl` | `DECIMAL(38,2)` |
| `health_facilities_damaged` | `BIGINT` |
| `health_facilities_destroyed` | `BIGINT` |
| `health_facilities_damage_brl` | `DECIMAL(38,2)` |
| `education_facilities_damaged` | `BIGINT` |
| `education_facilities_destroyed` | `BIGINT` |
| `education_facilities_damage_brl` | `DECIMAL(38,2)` |
| `service_facilities_damaged` | `BIGINT` |
| `service_facilities_destroyed` | `BIGINT` |
| `service_facilities_damage_brl` | `DECIMAL(38,2)` |
| `community_facilities_damaged` | `BIGINT` |
| `community_facilities_destroyed` | `BIGINT` |
| `community_facilities_damage_brl` | `DECIMAL(38,2)` |
| `infrastructure_works_damaged` | `BIGINT` |
| `infrastructure_works_destroyed` | `BIGINT` |
| `infrastructure_damage_brl` | `DECIMAL(38,2)` |
| `material_damage_total_brl` | `DECIMAL(38,2)` |
| `environmental_damage_description` | `VARCHAR` |
| `water_pollution_impact_source` | `VARCHAR` |
| `air_pollution_impact_source` | `VARCHAR` |
| `soil_pollution_impact_source` | `VARCHAR` |
| `water_depletion_impact_source` | `VARCHAR` |
| `protected_area_fire_impact_source` | `VARCHAR` |
| `public_loss_description` | `VARCHAR` |
| `public_health_emergency_loss_brl` | `DECIMAL(38,2)` |
| `public_water_supply_loss_brl` | `DECIMAL(38,2)` |
| `public_sewerage_loss_brl` | `DECIMAL(38,2)` |
| `public_waste_management_loss_brl` | `DECIMAL(38,2)` |
| `public_pest_control_loss_brl` | `DECIMAL(38,2)` |
| `public_energy_distribution_loss_brl` | `DECIMAL(38,2)` |
| `public_telecommunications_loss_brl` | `DECIMAL(38,2)` |
| `public_transport_loss_brl` | `DECIMAL(38,2)` |
| `public_fuel_distribution_loss_brl` | `DECIMAL(38,2)` |
| `public_safety_loss_brl` | `DECIMAL(38,2)` |
| `public_education_loss_brl` | `DECIMAL(38,2)` |
| `public_loss_total_brl` | `DECIMAL(38,2)` |
| `private_loss_description` | `VARCHAR` |
| `private_agriculture_loss_brl` | `DECIMAL(38,2)` |
| `private_livestock_loss_brl` | `DECIMAL(38,2)` |
| `private_industry_loss_brl` | `DECIMAL(38,2)` |
| `private_commerce_loss_brl` | `DECIMAL(38,2)` |
| `private_services_loss_brl` | `DECIMAL(38,2)` |
| `private_loss_total_brl` | `DECIMAL(38,2)` |
| `public_private_loss_total_brl` | `DECIMAL(38,2)` |
| `is_rain_related` | `BOOLEAN` |
| `is_hydrological` | `BOOLEAN` |
| `is_geological` | `BOOLEAN` |
| `classification_version` | `VARCHAR` |
| `is_protocol_format_valid` | `BOOLEAN` |
| `is_protocol_ibge_consistent` | `BOOLEAN` |
| `is_protocol_cobrade_consistent` | `BOOLEAN` |
| `is_event_after_registration` | `BOOLEAN` |
| `is_dim_municipality_match` | `BOOLEAN` |
| `monetary_values_are_corrected` | `BOOLEAN` |
| `monetary_correction_index` | `VARCHAR` |
| `monetary_reference_year` | `SMALLINT` |
| `source_corrected_material_damage_total_brl` | `DECIMAL(38,2)` |
| `source_release` | `VARCHAR` |
| `source_official_date` | `DATE` |
| `source_sha256` | `VARCHAR` |
| `source_workbook_sha256` | `VARCHAR` |
| `correction_log_sha256` | `VARCHAR` |
| `manual_sha256` | `VARCHAR` |
| `source_url` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` |

## Schema `snapshot_municipality_disaster_history`

| Nome | Tipo |
|---|---|
| `codigo_ibge` | `VARCHAR` |
| `reference_date` | `DATE` |
| `first_event_date` | `DATE` |
| `latest_event_date` | `DATE` |
| `event_count` | `BIGINT` |
| `rain_related_event_count` | `BIGINT` |
| `event_count_5y` | `BIGINT` |
| `event_count_10y` | `BIGINT` |
| `event_count_20y` | `BIGINT` |
| `rain_related_event_count_5y` | `BIGINT` |
| `rain_related_event_count_10y` | `BIGINT` |
| `rain_related_event_count_20y` | `BIGINT` |
| `deaths` | `HUGEINT` |
| `injured` | `HUGEINT` |
| `homeless` | `HUGEINT` |
| `displaced` | `HUGEINT` |
| `direct_human_damage_total` | `HUGEINT` |
| `reported_affected_total` | `HUGEINT` |
| `source_release` | `VARCHAR` |
| `source_sha256` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` |

## Schema `municipality_disaster_type_summary`

| Nome | Tipo |
|---|---|
| `codigo_ibge` | `VARCHAR` |
| `cobrade_code` | `VARCHAR` |
| `first_event_date` | `DATE` |
| `latest_event_date` | `DATE` |
| `event_count` | `BIGINT` |
| `deaths` | `HUGEINT` |
| `injured` | `HUGEINT` |
| `homeless` | `HUGEINT` |
| `displaced` | `HUGEINT` |
| `direct_human_damage_total` | `HUGEINT` |
| `reported_affected_total` | `HUGEINT` |
| `source_release` | `VARCHAR` |
| `source_sha256` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` |

## Schema `municipality_disaster_month_profile`

| Nome | Tipo |
|---|---|
| `codigo_ibge` | `VARCHAR` |
| `month` | `TINYINT` |
| `event_count` | `BIGINT` |
| `rain_related_event_count` | `BIGINT` |
| `source_release` | `VARCHAR` |
| `source_sha256` | `VARCHAR` |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` |

## Cautelas

- Os registros refletem o conhecimento informado no FIDE no momento do registro.
- A digitacao historica e a operacao do S2ID possuem metodologias diferentes.
- Reconhecimento federal e derivado somente de `Status = 'Reconhecido'`.
- Sazonalidade historica nao e probabilidade.
- Nenhuma tabela calcula risco, ranking, causalidade ou previsao.

O relatorio detalhado esta em `docs/atlas-data-quality-report.md`.
