# MapBiomas - Cobertura e Uso da Terra

## Fonte

- Fonte semantica: MapBiomas Brasil.
- Produto: Cobertura e Uso da Terra - Cobertura 30m.
- Pagina canonica: `https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/cobertura-30m/cobertura/`.
- Pagina de estatisticas: `https://brasil.mapbiomas.org/downloads/estatisticas/`.
- Pagina de legenda: `https://brasil.mapbiomas.org/downloads/codigos-de-legenda/`.
- Referencia de urbanizacao: `https://brasil.mapbiomas.org/iniciativas-e-produtos/cobertura-e-uso-da-terra/areas-urbanizadas/urbanizacao-anual/`.
- Resolucao original: 30 metros.
- Unidade estatistica ingerida: hectares.
- Colecao detectada: `Coleção 11`.
- Versao da tabela: `v1`.
- Serie detectada: `1985–2025`.
- Publicacao detectada: `2026-08-12`.
- Modo de descoberta: `automatic`.
- Asset GEE apenas para linhagem: `projects/mapbiomas-public/assets/brazil/lulc/collection11/mapbiomas_brazil_collection11_coverage_v3`.

O pipeline parte das paginas oficiais e exige concordancia entre a pagina do
produto e a pagina de estatisticas. Google Drive e somente infraestrutura de
distribuicao. `MAPBIOMAS_STATISTICS_URL` e `MAPBIOMAS_LEGEND_URL` sao overrides
de emergencia registrados como `discovery_mode=override`.

## Execucao

```bash
python -m src.mapbiomas
```

Na ausencia de mudanca de colecao, URLs, hashes e codigo do pipeline, uma nova
checagem e registrada mas os Parquets nao sao reconstruidos. Nova colecao
reconstroi toda a serie, nao apenas o ultimo ano, preserva os RAW anteriores e
gera relatorio de impacto.

## RAW e Schema Encontrado

O recurso oficial e um ZIP contendo XLSX. Folhas encontradas:
`('READ_ME', 'COVERAGE_11', 'PIVOT_COVERAGE', 'METADATA', 'LEGEND_CODE')`. A folha de dados possui
**77406** linhas, **6** biomas,
**27** estados, **5572** geocodigos
e anos em colunas `yAAAA`.

| Coluna original | Tipo aparente DuckDB |
|---|---|
| `ID` | `DOUBLE` |
| `country` | `VARCHAR` |
| `biome` | `VARCHAR` |
| `region` | `VARCHAR` |
| `state` | `VARCHAR` |
| `geocode` | `VARCHAR` |
| `municipality` | `VARCHAR` |
| `municipality-state` | `VARCHAR` |
| `class` | `DOUBLE` |
| `class_level_0` | `VARCHAR` |
| `class_level_1` | `VARCHAR` |
| `class_level_2` | `VARCHAR` |
| `class_level_3` | `VARCHAR` |
| `class_level_4` | `VARCHAR` |
| `y1985` | `DOUBLE` |
| `y1986` | `DOUBLE` |
| `y1987` | `DOUBLE` |
| `y1988` | `DOUBLE` |
| `y1989` | `DOUBLE` |
| `y1990` | `DOUBLE` |
| `y1991` | `DOUBLE` |
| `y1992` | `DOUBLE` |
| `y1993` | `DOUBLE` |
| `y1994` | `DOUBLE` |
| `y1995` | `DOUBLE` |
| `y1996` | `DOUBLE` |
| `y1997` | `DOUBLE` |
| `y1998` | `DOUBLE` |
| `y1999` | `DOUBLE` |
| `y2000` | `DOUBLE` |
| `y2001` | `DOUBLE` |
| `y2002` | `DOUBLE` |
| `y2003` | `DOUBLE` |
| `y2004` | `DOUBLE` |
| `y2005` | `DOUBLE` |
| `y2006` | `DOUBLE` |
| `y2007` | `DOUBLE` |
| `y2008` | `DOUBLE` |
| `y2009` | `DOUBLE` |
| `y2010` | `DOUBLE` |
| `y2011` | `DOUBLE` |
| `y2012` | `DOUBLE` |
| `y2013` | `DOUBLE` |
| `y2014` | `DOUBLE` |
| `y2015` | `DOUBLE` |
| `y2016` | `DOUBLE` |
| `y2017` | `DOUBLE` |
| `y2018` | `DOUBLE` |
| `y2019` | `DOUBLE` |
| `y2020` | `DOUBLE` |
| `y2021` | `DOUBLE` |
| `y2022` | `DOUBLE` |
| `y2023` | `DOUBLE` |
| `y2024` | `DOUBLE` |
| `y2025` | `DOUBLE` |

A legenda e CSV `utf-8`, delimitado por
`,`, com colunas `('class_id', 'class_name_pt_br', 'class_name_en', 'hex_code')`.
O XLSX possui as classes `(0, 13)` ausentes do
CSV; o CSV possui `(77,)` ausentes das estatisticas.
Nesses casos a hierarquia oficial do workbook e preservada e sua origem fica
explicita em `mapbiomas_class_legend.parquet`.

## Granularidades

- RAW: uma linha larga por geocodigo, bioma e classe terminal, com anos em colunas.
- SILVER: colecao x geocodigo x bioma x ano x classe.
- FACT: municipio canonico x ano x classe, apos `SUM` de todos os biomas.
- SNAPSHOT: municipio canonico x ano.
- CHANGE: municipio canonico, com primeiro/ultimo ano e janelas dinamicas.

Existem **898** geocodigos em mais
de um bioma. Nenhum bioma e escolhido por `MAX` ou por prioridade. A unica
duplicidade no grao RAW e consolidada por soma na SILVER, que preserva
`source_row_count`, `source_state_names` e `source_region_names`.

## Hierarquia e Agregacoes

A tabela estatistica contem classes terminais. `class_level` e derivado do ultimo
nivel distinto em `class_level_1..4`; classes pai nao sao somadas aos filhos.

- Area urbanizada: classe `24`, resolvida no CSV e conferida na pagina de Urbanizacao Anual.
- Agua: classe `33` (`Rio, Lago e Oceano`).
- Campo alagado/area pantanosa: classe `11`.
- `native_vegetation_class_ids`: `(3, 4, 5, 6, 7, 11, 12, 13, 29, 32, 49, 50, 84)`.
- `agriculture_livestock_class_ids`: `(9, 15, 20, 21, 35, 39, 40, 41, 46, 47, 48, 62)`.
- Classes excluidas do denominador como `Not Observed`: `(0,)`.

Vegetacao nativa e derivada dos ramos oficiais `Forest` e
`Herbaceous and Shrubby Vegetation`. Agropecuaria e derivada de todos os filhos
terminais de `Farming`. As listas sao recalculadas e versionadas por colecao.

`mapped_area_ha` soma classes terminais mutuamente exclusivas, exceto `Not
Observed`. A maior variacao observada entre anos foi
`0.133448%`; apos observar a
distribuicao, adotou-se 0,1% como alerta e 1% como falha.

Os percentuais selecionados nao somam necessariamente 100%. Em particular,
campo alagado e area pantanosa integra o ramo de vegetacao nativa e aparece
tambem como indicador proprio.

## Matching Municipal

- Geocodigos MapBiomas: `5572`.
- Codigos da dimensao: `5571`.
- Matched: `5570`.
- Cobertura: `99.982050%`.
- MapBiomas sem dimensao: `['4300001', '4300002']`.
- Dimensao sem MapBiomas: `['2605459']`.

Os codigos extras atuais representam Lagoa Mirim e Lagoa dos Patos. Fernando de
Noronha nao aparece na tabela estatistica. Nenhum matching por nome e aplicado.

## Schema FACT

| Nome | Tipo | Descricao |
|---|---|---|
| `codigo_ibge` | `VARCHAR` | Codigo territorial usado no relacionamento com dim_municipality. |
| `year` | `INTEGER` | Ano da classificacao MapBiomas. |
| `class_id` | `INTEGER` | Codigo oficial da classe de cobertura e uso da terra. |
| `class_name` | `VARCHAR` | Nome oficial da classe; fallback auditavel do workbook quando ausente no CSV. |
| `class_level` | `INTEGER` | Nivel terminal derivado da hierarquia oficial do workbook. |
| `area_ha` | `DOUBLE` | Area classificada em hectares. |
| `area_km2` | `DOUBLE` | Area em quilometros quadrados, calculada como hectares / 100. |
| `collection_id` | `VARCHAR` | Identificador da colecao MapBiomas. |
| `collection_version` | `VARCHAR` | Versao da tabela estatistica na pagina oficial. |
| `source_sha256` | `VARCHAR` | SHA-256 do arquivo ZIP estatistico oficial. |
| `source_publication_date` | `DATE` | Data de publicacao declarada na pagina oficial. |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` | Timestamp UTC da execucao que materializou os dados. |

## Schema Snapshot

| Nome | Tipo | Descricao |
|---|---|---|
| `codigo_ibge` | `VARCHAR` | Codigo territorial usado no relacionamento com dim_municipality. |
| `year` | `INTEGER` | Ano da classificacao MapBiomas. |
| `mapped_area_ha` | `DOUBLE` | Soma das classes terminais, excluindo Not Observed. |
| `urban_area_ha` | `DOUBLE` | Area classificada como Area Urbanizada, em hectares. |
| `urban_area_km2` | `DOUBLE` | Area classificada como Area Urbanizada, em km2. |
| `urban_area_pct` | `DOUBLE` | Area Urbanizada dividida pela area mapeada, em percentual. |
| `native_vegetation_area_ha` | `DOUBLE` | Soma dos ramos naturais selecionados, em hectares. |
| `native_vegetation_area_km2` | `DOUBLE` | Soma dos ramos naturais selecionados, em km2. |
| `native_vegetation_area_pct` | `DOUBLE` | Vegetacao nativa dividida pela area mapeada. |
| `agriculture_livestock_area_ha` | `DOUBLE` | Ramo terminal Agropecuaria/Farming, em hectares. |
| `agriculture_livestock_area_km2` | `DOUBLE` | Ramo terminal Agropecuaria/Farming, em km2. |
| `agriculture_livestock_area_pct` | `DOUBLE` | Agropecuaria dividida pela area mapeada. |
| `water_area_ha` | `DOUBLE` | Area de Rio, Lago e Oceano, em hectares. |
| `water_area_km2` | `DOUBLE` | Area de Rio, Lago e Oceano, em km2. |
| `water_area_pct` | `DOUBLE` | Rio, Lago e Oceano dividido pela area mapeada. |
| `wetland_area_ha` | `DOUBLE` | Campo Alagado e Area Pantanosa, em hectares. |
| `wetland_area_km2` | `DOUBLE` | Campo Alagado e Area Pantanosa, em km2. |
| `wetland_area_pct` | `DOUBLE` | Campo Alagado e Area Pantanosa dividido pela area mapeada. |
| `collection_id` | `VARCHAR` | Identificador da colecao MapBiomas. |
| `collection_version` | `VARCHAR` | Versao da tabela estatistica na pagina oficial. |
| `source_sha256` | `VARCHAR` | SHA-256 do arquivo ZIP estatistico oficial. |
| `source_publication_date` | `DATE` | Data de publicacao declarada na pagina oficial. |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` | Timestamp UTC da execucao que materializou os dados. |

## Schema Changes

| Nome | Tipo | Descricao |
|---|---|---|
| `codigo_ibge` | `VARCHAR` | Codigo territorial usado no relacionamento com dim_municipality. |
| `first_year` | `INTEGER` | First year. |
| `latest_year` | `INTEGER` | Latest year. |
| `reference_year_5y` | `INTEGER` | Reference year 5y. |
| `reference_year_10y` | `INTEGER` | Reference year 10y. |
| `reference_year_20y` | `INTEGER` | Reference year 20y. |
| `urban_area_first_year_ha` | `DOUBLE` | Urban area first year ha. |
| `urban_area_latest_year_ha` | `DOUBLE` | Urban area latest year ha. |
| `urban_area_change_ha` | `DOUBLE` | Urban area change ha. |
| `urban_area_change_pct` | `DOUBLE` | Urban area change pct. |
| `urban_change_5y_ha` | `DOUBLE` | Urban change 5y ha. |
| `urban_change_5y_pct` | `DOUBLE` | Urban change 5y pct. |
| `urban_change_10y_ha` | `DOUBLE` | Urban change 10y ha. |
| `urban_change_10y_pct` | `DOUBLE` | Urban change 10y pct. |
| `urban_change_20y_ha` | `DOUBLE` | Urban change 20y ha. |
| `urban_change_20y_pct` | `DOUBLE` | Urban change 20y pct. |
| `native_vegetation_first_year_ha` | `DOUBLE` | Native vegetation first year ha. |
| `native_vegetation_latest_year_ha` | `DOUBLE` | Native vegetation latest year ha. |
| `native_vegetation_change_ha` | `DOUBLE` | Native vegetation change ha. |
| `native_vegetation_change_pct` | `DOUBLE` | Native vegetation change pct. |
| `native_vegetation_change_5y_ha` | `DOUBLE` | Native vegetation change 5y ha. |
| `native_vegetation_change_5y_pct` | `DOUBLE` | Native vegetation change 5y pct. |
| `native_vegetation_change_10y_ha` | `DOUBLE` | Native vegetation change 10y ha. |
| `native_vegetation_change_10y_pct` | `DOUBLE` | Native vegetation change 10y pct. |
| `native_vegetation_change_20y_ha` | `DOUBLE` | Native vegetation change 20y ha. |
| `native_vegetation_change_20y_pct` | `DOUBLE` | Native vegetation change 20y pct. |
| `water_area_change_10y_ha` | `DOUBLE` | Water area change 10y ha. |
| `wetland_area_change_10y_ha` | `DOUBLE` | Wetland area change 10y ha. |
| `collection_id` | `VARCHAR` | Identificador da colecao MapBiomas. |
| `collection_version` | `VARCHAR` | Versao da tabela estatistica na pagina oficial. |
| `source_sha256` | `VARCHAR` | SHA-256 do arquivo ZIP estatistico oficial. |
| `source_publication_date` | `DATE` | Data de publicacao declarada na pagina oficial. |
| `ingested_at` | `TIMESTAMP WITH TIME ZONE` | Timestamp UTC da execucao que materializou os dados. |

## Cautelas Metodologicas

- MapBiomas e uma classificacao por sensoriamento remoto, nao um cadastro fisico do solo.
- Colecoes novas podem revisar toda a serie historica.
- Area urbanizada nao e sinônimo de superficie impermeabilizada.
- Campo alagado e area pantanosa nao e mapa de risco.
- Agua superficial nao equivale a disponibilidade hidrica.
- Correlacao temporal nao demonstra causalidade.
- Nenhum indicador desta camada mede risco, vulnerabilidade ou resiliencia.
- GeoTIFF e Google Earth Engine nao sao usados neste pipeline.

O relatorio completo esta em `docs/mapbiomas-data-quality-report.md` e o
manifest estruturado em `data/gold/mapbiomas_data_quality_report.json`.
