# Antes da Chuva

> **Estado da migração em 3 de setembro de 2026:** este documento descreve o
> produto de dados e registra a baseline validada no projeto de origem. O
> repositório consolidado contém o código, os testes e os manifests compactos,
> mas não contém RAW, SILVER, GOLD nem Parquets. Os números `PASS` abaixo não
> são uma execução nova neste clone. Consultas aos artefatos e validações de
> saídas ficam bloqueadas até que os dados sejam materializados localmente com
> acesso às fontes oficiais e espaço em disco.

Data product local, reproduzivel e auditavel para integrar dados publicos sobre municipios brasileiros.

O projeto esta sendo construido em camadas. A base territorial canonica vem do IBGE e todas as fontes observacionais devem, sempre que possivel, terminar relacionadas ao mesmo `codigo_ibge`. A finalidade e permitir perguntas sobre territorio, cobertura da terra, desastres, capacidade municipal e recursos publicos sem misturar evidencias de fontes diferentes nem transformar correlacoes em causalidade.

Neste momento existem tres produtos implementados:

| Produto | Fonte oficial | Papel no modelo | Status |
|---|---|---|---|
| `dim_municipality` | IBGE | Dimensao territorial canonica vigente | Produzido e validado |
| Cobertura e uso da terra | MapBiomas Brasil | Fatos e snapshots temporais por municipio | Produzido e validado |
| Historico de desastres | Atlas Digital/S2ID | Eventos oficiais, impactos e perfis historicos | Produzido e validado |

As proximas fontes planejadas incluem Indicador de Capacidade Municipal, Transferegov, SINISA e outros dados publicos relevantes. Elas ainda nao fazem parte dos pipelines atuais.

## Inicio Rapido

Este repositorio e um produto de dados em lote. Ele nao inicia uma API ou um
servidor: os comandos abaixo consultam as fontes oficiais, validam os dados e
materializam arquivos Parquet em `data/silver/` e `data/gold/`.

Execute a partir da raiz do repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python -m pytest -q
```

A ordem importa: MapBiomas e Atlas dependem de
`data/gold/dim_municipality.parquet`, produzido pela primeira etapa.

Esses comandos baixam fontes oficiais e materializam arquivos locais ignorados
pelo Git. Em um clone sem esses dados, execute primeiro a sequência completa;
as consultas e os testes de saídas materializadas não podem usar os manifests
como substitutos dos Parquets.

Se os Parquets ja estiverem materializados e o objetivo for apenas consulta-los,
nao e necessario executar novamente as cargas. Consulte o guia
[`como-consumir.md`](como-consumir.md).

## Baseline Validada na Origem

Ultima execucao completa validada: **2 de setembro de 2026, 21:06 UTC**.

| Indicador | Resultado atual |
|---|---:|
| Localidades no nivel municipal da dimensao IBGE | 5.571 |
| Municipios stricto sensu | 5.569 |
| Unidades da Federacao | 27 |
| Grandes Regioes | 5 |
| Colecao MapBiomas detectada | 11 |
| Versao da tabela MapBiomas | v1 |
| Serie MapBiomas | 1985-2025 |
| Geocodigos presentes no MapBiomas | 5.572 |
| Municipios MapBiomas associados a dimensao | 5.570 |
| Cobertura da `dim_municipality` pelo MapBiomas | 99,982050% |
| Release Atlas/S2ID | atlas_1991_2025_v1.1_2026-08-06 |
| Registros oficiais Atlas | 76.190 |
| Municipios com registro Atlas | 5.256 |
| Cobertura da `dim_municipality` pelo Atlas | 94,345719% |
| Tipos COBRADE na dimensao Atlas | 65 |
| Testes automatizados | 15 aprovados |
| Data quality IBGE | PASS |
| Data quality MapBiomas | PASS |
| Data quality Atlas/S2ID | PASS |
| Ultima carga MapBiomas | PASS |
| Ultima carga Atlas/S2ID | PASS |

Os valores acima descrevem os artefatos materializados na origem. Os manifests e
relatorios de qualidade são referência histórica; não confirmam a presença dos
artefatos neste clone.

## Objetivo Do Produto

O projeto pretende oferecer uma camada comum para responder perguntas como:

- quais unidades territoriais municipais estao vigentes;
- como cada fonte publica se relaciona ao territorio oficial do IBGE;
- como a cobertura e o uso da terra de um municipio mudaram ao longo do tempo;
- quais fatos sobre urbanizacao, vegetacao natural, agua e areas umidas sao observaveis;
- quais divergencias de codigo, cobertura ou metodologia existem entre fontes;
- de qual arquivo, versao, colecao e execucao cada numero foi derivado.
- quais desastres e impactos foram registrados oficialmente em cada municipio.

O principio central e separar tres coisas:

1. identidade territorial;
2. fatos observacionais;
3. interpretacoes ou indicadores derivados.

`dim_municipality` resolve a identidade territorial vigente. MapBiomas fornece fatos observacionais de cobertura e uso da terra. Atlas/S2ID fornece registros historicos oficiais de desastres e impactos. Interpretacoes sobre risco, vulnerabilidade, probabilidade ou causalidade nao sao produzidas nesta fase.

## Principios De Engenharia

- `codigo_ibge` e a chave territorial principal.
- Nome de municipio e atributo, nunca chave principal de integracao.
- Codigos administrativos sao armazenados como strings.
- RAW preserva evidencia da fonte sem limpeza semantica.
- SILVER normaliza dados e preserva atributos necessarios para auditoria.
- GOLD publica apenas estruturas analiticas com grao conhecido.
- Toda GOLD possui linhagem suficiente para identificar arquivo, colecao e ingestao.
- Quantidades oficiais nao sao fixadas silenciosamente no codigo quando podem ser descobertas na fonte.
- Mudancas de colecao reprocessam a serie completa, em vez de acrescentar apenas o ultimo ano.
- Diferencas entre fontes sao reportadas, nao mascaradas por matching de nome.
- Pipelines falham explicitamente quando o schema ou a descoberta deixam de ser confiaveis.
- O volume atual e processado localmente com Python e DuckDB.

## O Que O Projeto Nao Faz

Os artefatos atuais nao calculam:

- score de risco;
- indice de enchente;
- impermeabilizacao estimada;
- vulnerabilidade ou resiliencia;
- risco climatico;
- probabilidade de desastre;
- populacao exposta;
- area urbana em area de risco;
- distancia ate rios;
- declividade;
- area construida em varzea.

MapBiomas descreve cobertura e uso da terra classificados por sensoriamento remoto. Aumento de area urbanizada nao demonstra, isoladamente, aumento de risco. Area urbanizada nao e sinonimo de superficie impermeabilizada. Campo alagado nao e mapa de risco. Agua superficial nao equivale a disponibilidade hidrica.

## Modelo De Dados

```text
dim_municipality (PK logica: codigo_ibge)
|
|-- fact_municipality_land_cover (municipio x ano x classe)
|-- snapshot_municipality_land_cover (municipio x ano)
|-- municipality_land_cover_change (municipio)
|-- fact_disaster_event (municipio x registro oficial)
|-- snapshot_municipality_disaster_history (municipio x data de referencia)
|-- municipality_disaster_type_summary (municipio x COBRADE)
`-- municipality_disaster_month_profile (municipio x mes)

municipality_disaster_type_summary.cobrade_code
`-- dim_disaster_type.cobrade_code
```

O relacionamento territorial e sempre feito por `codigo_ibge`. Os nomes oficiais
continuam disponiveis na dimensao para exibicao e auditoria. Para escolher a
tabela certa e preservar sua granularidade, consulte
[`como-consumir.md`](como-consumir.md).

## Arquitetura De Camadas

```text
Fontes oficiais
      |
      v
data/raw/       bytes originais, paginas de descoberta e manifests
      |
      v
data/silver/    normalizacao, hierarquia e atributos de auditoria
      |
      v
data/gold/      dimensoes, fatos, snapshots, mudancas e quality reports
```

### RAW

Responsabilidades:

- preservar os bytes recebidos;
- registrar URL de descoberta e URL resolvida;
- registrar nome original, headers HTTP e tamanho;
- calcular SHA-256;
- manter colecao, versao e data de publicacao quando disponiveis;
- nao renomear colunas nem alterar valores da fonte;
- manter colecoes anteriores auditaveis.

### SILVER

Responsabilidades:

- converter codigos para tipos consistentes;
- normalizar estruturas aninhadas ou largas;
- preservar classificacoes legadas quando uteis para auditoria;
- preservar bioma e hierarquia de classe;
- registrar discrepancias e consolidacoes da fonte;
- preparar graos unicos antes da publicacao analitica.

### GOLD

Responsabilidades:

- expor tabelas com granularidade declarada;
- relacionar fatos ao `codigo_ibge` canonico;
- remover dimensoes de fonte que ja foram corretamente agregadas;
- fornecer linhagem tecnica em todas as tabelas;
- publicar somente depois das validacoes obrigatorias.

## Catalogo De Artefatos

### Dimensao Territorial

| Artefato | Camada | Granularidade | Linhas atuais |
|---|---|---|---:|
| `data/raw/raw_ibge_municipalities.json` | RAW | Resposta integral da API | 5.571 objetos |
| `data/raw/raw_ibge_municipalities_metadata.json` | RAW | Manifest da captura | 1 manifest |
| `data/silver/silver_ibge_municipalities.parquet` | SILVER | Uma linha por localidade municipal | 5.571 |
| `data/gold/dim_municipality.parquet` | GOLD | Uma linha por localidade municipal vigente | 5.571 |
| `data/gold/dim_municipality.csv` | GOLD | Copia para inspecao manual | 5.571 |
| `data/gold/data_quality_report.json` | GOLD | Relatorio estruturado da dimensao | 1 relatorio |

### MapBiomas

| Artefato | Camada | Granularidade | Linhas atuais |
|---|---|---|---:|
| `data/raw/mapbiomas/collection_11/` | RAW | Arquivos, paginas e manifests da colecao | Colecao completa |
| `data/silver/mapbiomas_land_cover.parquet` | SILVER | Colecao x geocodigo x bioma x ano x classe | 3.173.605 |
| `data/silver/mapbiomas_class_legend.parquet` | SILVER | Colecao x classe | 35 |
| `data/gold/fact_municipality_land_cover.parquet` | GOLD | Municipio x ano x classe | 2.798.168 |
| `data/gold/snapshot_municipality_land_cover.parquet` | GOLD | Municipio x ano | 228.370 |
| `data/gold/municipality_land_cover_change.parquet` | GOLD | Municipio | 5.570 |
| `data/gold/mapbiomas_data_quality_report.json` | GOLD | Relatorio estruturado MapBiomas | 1 relatorio |
| `data/manifests/mapbiomas/latest_successful_run.json` | Manifest | Ultima execucao bem-sucedida | 1 manifest |

### Atlas Digital / S2ID

| Artefato | Camada | Granularidade | Linhas atuais |
|---|---|---|---:|
| `data/raw/atlas/atlas_1991_2025_v1.1_2026-08-06/` | RAW | CSV, XLSX, manual, log e manifests preservados | 1 release |
| `data/silver/silver_disaster_event.parquet` | SILVER | Uma linha por registro oficial | 76.190 |
| `data/silver/atlas_monetary_correction_factor.parquet` | SILVER | Um fator IGP-DI por ano de referencia | 36 |
| `data/silver/dim_disaster_type.parquet` | SILVER | Uma linha por COBRADE oficial | 65 |
| `data/gold/fact_disaster_event.parquet` | GOLD | Municipio x registro oficial | 76.190 |
| `data/gold/snapshot_municipality_disaster_history.parquet` | GOLD | Municipio x data de referencia | 5.571 |
| `data/gold/municipality_disaster_type_summary.parquet` | GOLD | Municipio x COBRADE | 22.719 |
| `data/gold/municipality_disaster_month_profile.parquet` | GOLD | Municipio x mes | 66.852 |
| `data/gold/atlas_data_quality_report.json` | GOLD | Relatorio estruturado Atlas | 1 relatorio |
| `data/manifests/atlas/latest_successful_run.json` | Manifest | Ultima execucao bem-sucedida | 1 manifest |

## Estrutura Do Repositorio

```text
.
|-- data/
|   |-- raw/
|   |   |-- mapbiomas/
|   |   |-- atlas/
|   |   `-- raw_ibge_municipalities.json
|   |-- silver/
|   |-- gold/
|   `-- manifests/
|-- docs/
|   |-- como-consumir.md
|   |-- schema.md
|   |-- source-and-territorial-decisions.md
|   |-- data-quality-report.md
|   |-- mapbiomas.md
|   |-- mapbiomas-data-quality-report.md
|   |-- atlas.md
|   `-- atlas-data-quality-report.md
|-- src/
|   |-- contracts/
|   |-- extract/
|   |-- transform/
|   |-- validation/
|   |-- pipeline.py
|   |-- mapbiomas.py
|   `-- atlas.py
|-- tests/
|-- requirements.txt
`-- README.md
```

## Dimensao Territorial Canonica

### Fonte

Fonte primaria: API de Localidades v1, oficial do IBGE.

```text
https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id
```

A resposta materializada em 1 de setembro de 2026 possui 5.571 unidades no nivel analitico municipal. A Divisao Territorial Brasileira 2025 descreve esse universo como 5.569 municipios, mais o Distrito Federal e o distrito estadual de Fernando de Noronha.

A quantidade nao esta fixa no pipeline. A GOLD e comparada com a quantidade e com o conjunto de codigos retornados na propria resposta oficial.

### Grao E Chave

Granularidade:

```text
1 linha por localidade vigente no nivel municipal da API do IBGE
```

Chave primaria logica:

```text
codigo_ibge
```

Principais atributos:

- nome oficial do municipio;
- nome normalizado somente para busca auxiliar;
- UF e codigo da UF;
- Grande Regiao e codigo da regiao;
- Regiao Geografica Imediata;
- Regiao Geografica Intermediaria;
- tipo da unidade territorial;
- fonte, URL e timestamps de linhagem.

O schema coluna a coluna esta em [`schema.md`](schema.md).

### Hierarquia Territorial

Regioes geograficas imediatas e intermediarias fazem parte da GOLD por serem a divisao regional vigente.

Mesorregioes e microrregioes ficam somente na SILVER porque foram substituidas progressivamente e ja nao sao completas para todos os municipios. Boa Esperanca do Norte/MT, por exemplo, aparece sem microrregiao na API atual.

### Casos Especiais

| Codigo | Unidade | Tratamento |
|---|---|---|
| `5300108` | Brasilia/DF | Mantida como `distrito_federal` no nivel analitico municipal |
| `2605459` | Fernando de Noronha/PE | Mantida como `distrito_estadual` |
| `5101837` | Boa Esperanca do Norte/MT | Municipio vigente, sem microrregiao legada na fonte |

### Qualidade Atual

- 5.571 linhas;
- 5.571 codigos distintos;
- zero duplicados de `codigo_ibge`;
- zero nulos nos campos territoriais obrigatorios;
- 27 UFs;
- 5 Grandes Regioes;
- uma UF por municipio;
- uma regiao por UF;
- hierarquia imediata e intermediaria completa;
- exemplos territoriais obrigatorios presentes;
- status final `PASS`.

`source_updated_at` permanece nulo porque a API nao publica versao, data de referencia, `Last-Modified` ou `ETag`. A captura e rastreada por `ingested_at`, RAW e SHA-256.

### Pipeline

```text
API IBGE
   |
   v
RAW JSON + manifest
   |
   v
SILVER territorial normalizada
   |
   v
dim_municipality + CSV + quality report
```

Entrada principal:

```bash
python -m src.pipeline
```

## MapBiomas Cobertura E Uso Da Terra

### Papel No Produto

MapBiomas responde:

> Como o territorio deste municipio esta coberto e como essa cobertura mudou ao longo do tempo?

MapBiomas nao responde isoladamente:

> Qual e o risco de enchente deste municipio?

As tabelas MapBiomas sao produtos temporais separados e nao adicionam colunas a `dim_municipality`.

### Descoberta Da Fonte

O pipeline consulta as paginas oficiais para descobrir a colecao vigente, a tabela estatistica municipal e a legenda:

```text
Pagina oficial Cobertura 30m
          |
          v
colecao vigente e serie temporal
          |
          v
pagina oficial de estatisticas
          |
          v
tabela BIOME_STATE_MUNICIPALITY
          |
          v
pagina oficial de codigos de legenda
```

Estado atual descoberto automaticamente:

| Propriedade | Valor |
|---|---|
| Colecao | 11 |
| Versao da tabela | v1 |
| Serie | 1985-2025 |
| Publicacao da tabela | 12 de agosto de 2026 |
| Resolucao original | 30 metros |
| Unidade estatistica | hectare |
| Modo de descoberta | automatic |

O arquivo estatistico e distribuido oficialmente por Google Drive, mas a fonte semantica continua sendo MapBiomas Brasil. O pipeline resolve o formulario de confirmacao para arquivos grandes, valida o ZIP e registra a URL de descoberta, a URL resolvida, headers e SHA-256.

Overrides de emergencia:

```bash
MAPBIOMAS_STATISTICS_URL="https://..." python -m src.mapbiomas
MAPBIOMAS_LEGEND_URL="https://..." python -m src.mapbiomas
```

Quando um override e usado, o manifest registra `discovery_mode=override`.

### RAW MapBiomas

Estrutura atual:

```text
data/raw/mapbiomas/collection_11/
|-- discovery/
|   |-- coverage.html
|   |-- statistics.html
|   |-- legend.html
|   `-- urbanization.html
|-- statistics/<prefixo_sha256>/
|   |-- MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE_MUNICIPALITY.zip
|   `-- MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE_MUNICIPALITY.xlsx
|-- legend/<prefixo_sha256>/
|   `-- legend_code_mapbiomas_brazil_collection_11.csv
`-- manifests/
    |-- statistics.json
    `-- legend.json
```

SHA-256 atual do ZIP estatistico:

```text
c223fd84dcdd21e49d651788ff5a726a7e3aa04d2eab730e99407dd80a8d3e30
```

SHA-256 atual da legenda:

```text
603239c5de7cca95799c788ab553a73ec3fc16477f681f63bb5af191d2f54dbe
```

Os caminhos sao content-addressed. Uma nova versao fisica nao substitui silenciosamente a evidencia anterior.

### Schema Real Encontrado

O ZIP contem um XLSX com as folhas:

```text
READ_ME
COVERAGE_11
PIVOT_COVERAGE
METADATA
LEGEND_CODE
```

A folha `COVERAGE_11` possui 77.406 linhas largas e 41 colunas anuais, de `y1985` ate `y2025`. Os campos territoriais e classificatorios sao:

```text
ID
country
biome
region
state
geocode
municipality
municipality-state
class
class_level_0
class_level_1
class_level_2
class_level_3
class_level_4
```

A inspecao completa, incluindo tipos, esta em [`mapbiomas.md`](mapbiomas.md).

### Municipio E Bioma

O arquivo de origem possui grao territorial por bioma. Um municipio pode intersectar varios biomas. Na fonte atual, 898 geocodigos aparecem em mais de um bioma.

A SILVER preserva o bioma:

```text
colecao x codigo_ibge x bioma x ano x classe
```

A FACT municipal soma todos os componentes:

```sql
SELECT
    codigo_ibge,
    year,
    class_id,
    SUM(area_ha) AS area_ha
FROM silver_mapbiomas_land_cover
GROUP BY codigo_ibge, year, class_id;
```

Nenhum bioma e escolhido por `MAX`, prioridade ou conveniencia.

### Hierarquia De Classes

O XLSX fornece `class_level_0` ate `class_level_4`. A tabela estatistica atual contem classes terminais, e `class_level` e derivado do ultimo nivel distinto da hierarquia. Isso evita somar simultaneamente classes pai e filhas.

As agregacoes de produto sao resolvidas a partir da legenda e da hierarquia oficiais da colecao:

| Indicador | Regra atual |
|---|---|
| Area urbanizada | Classe oficial `24` |
| Agua | Classe `33`, Rio, Lago e Oceano |
| Campo alagado/area pantanosa | Classe `11` |
| Vegetacao nativa | Filhos terminais dos ramos `Forest` e `Herbaceous and Shrubby Vegetation` |
| Agropecuaria | Filhos terminais do ramo `Farming` |
| Area mapeada | Soma das classes terminais, exceto `Not Observed` |

Composicao atual de vegetacao nativa:

```text
[3, 4, 5, 6, 7, 11, 12, 13, 29, 32, 49, 50, 84]
```

Composicao atual de agropecuaria:

```text
[9, 15, 20, 21, 35, 39, 40, 41, 46, 47, 48, 62]
```

Essas listas nao sao assumidas como permanentes. Elas sao recalculadas e versionadas por colecao.

Os percentuais selecionados nao precisam somar 100%. Campo alagado e area pantanosa, por exemplo, integra o ramo de vegetacao nativa e tambem aparece como indicador proprio.

### Tabelas GOLD MapBiomas

#### `fact_municipality_land_cover`

Granularidade:

```text
codigo_ibge x year x class_id
```

Uso recomendado:

- analisar qualquer classe terminal;
- construir series anuais;
- comparar composicao entre classes;
- auditar indicadores do snapshot.

Principais medidas:

```text
area_ha
area_km2
```

#### `snapshot_municipality_land_cover`

Granularidade:

```text
codigo_ibge x year
```

Indicadores publicados:

```text
mapped_area_ha
urban_area_ha
urban_area_km2
urban_area_pct
native_vegetation_area_ha
native_vegetation_area_km2
native_vegetation_area_pct
agriculture_livestock_area_ha
agriculture_livestock_area_km2
agriculture_livestock_area_pct
water_area_ha
water_area_km2
water_area_pct
wetland_area_ha
wetland_area_km2
wetland_area_pct
```

#### `municipality_land_cover_change`

Granularidade:

```text
codigo_ibge
```

A tabela usa dinamicamente o primeiro e o ultimo ano da colecao. Tambem calcula janelas de 5, 10 e 20 anos a partir do ultimo ano detectado.

Principais grupos de medidas:

- area urbana no primeiro e no ultimo ano;
- mudanca urbana absoluta e percentual;
- mudanca urbana em 5, 10 e 20 anos;
- vegetacao nativa no primeiro e no ultimo ano;
- mudanca de vegetacao nativa absoluta e percentual;
- mudanca de vegetacao nativa em 5, 10 e 20 anos;
- mudanca absoluta de agua em 10 anos;
- mudanca absoluta de area umida em 10 anos.

Divisoes percentuais por uma area inicial igual a zero retornam `NULL`, nunca infinito.

### Matching Com A Dimensao

Resultado atual:

| Metrica | Valor |
|---|---:|
| Codigos distintos na tabela MapBiomas | 5.572 |
| Codigos na `dim_municipality` | 5.571 |
| Codigos associados | 5.570 |
| Cobertura da dimensao | 99,982050% |

MapBiomas sem correspondencia na dimensao:

| Codigo | Unidade da fonte |
|---|---|
| `4300001` | Lagoa Mirim |
| `4300002` | Lagoa dos Patos |

Dimensao sem observacao MapBiomas:

| Codigo | Unidade |
|---|---|
| `2605459` | Fernando de Noronha |

Os dois recortes lacustres permanecem na SILVER para auditoria, mas nao entram nas GOLD municipais. Fernando de Noronha permanece na dimensao sem uma observacao fabricada. Nenhum dos casos e resolvido por nome.

### Anomalias Documentadas Da Fonte

#### Legenda

O XLSX estatistico contem as classes `0` e `13`, ausentes do CSV oficial de legenda. O CSV possui a classe `77`, ausente da tabela estatistica.

O pipeline nao ignora a diferenca. Classes presentes apenas no XLSX usam o nome e a hierarquia do workbook oficial, com `class_name_source='statistics_workbook_hierarchy'`. A tabela `mapbiomas_class_legend.parquet` registra a origem de cada nome e os hashes dos dois recursos.

#### Duplicidade Territorial

A fonte possui uma duplicidade no grao `geocode + biome + class` para Ibateguara/AL, classe 15. Uma das linhas aparece com estado de Pernambuco, embora o geocodigo e o rotulo municipal sejam de Alagoas.

A SILVER consolida as duas linhas por soma e preserva:

```text
source_row_count
source_state_names
source_region_names
```

O RAW continua sendo a evidencia integral da inconsistencia.

### Qualidade MapBiomas

Validacoes executadas:

- arquivos RAW existentes, nao vazios e legiveis;
- ZIP e XLSX validos;
- SHA-256 conferido;
- serie anual completa e sem lacunas;
- campos obrigatorios da SILVER sem nulos;
- `area_ha >= 0`;
- grao SILVER unico;
- reconciliacao entre RAW largo e SILVER longa;
- cobertura de `dim_municipality` acima de 99%;
- grao FACT unico;
- soma dos biomas reconciliada com a FACT;
- classes de indicadores presentes na hierarquia oficial;
- area municipal mapeada positiva;
- estabilidade temporal da area mapeada;
- percentuais entre 0 e 100;
- quatro municipios de referencia presentes.

A maior variacao observada da area mapeada entre anos foi 0,133448%. Depois de observar a distribuicao, o projeto adotou:

| Nivel | Limite |
|---|---:|
| Alerta | acima de 0,1% |
| Falha | acima de 1% |

Uma unidade ultrapassa o limite de alerta e nenhuma ultrapassa o limite de falha.

### Idempotencia E Novas Colecoes

Uma execucao e considerada sem mudanca quando permanecem iguais:

```text
collection_id
collection_version
statistics_url
statistics_sha256
legend_url
legend_sha256
pipeline_fingerprint
```

Quando tudo permanece igual e os artefatos existem, o pipeline:

- registra uma nova checagem;
- valida a existencia do relatorio anterior com `PASS`;
- nao reconstroi os Parquets;
- publica um run manifest com status `NO_CHANGE`.

A verificacao atual executou primeiro `PASS` e depois `NO_CHANGE`, com hashes de saida identicos.

Quando uma colecao nova for descoberta, o pipeline esta preparado para:

1. preservar o novo RAW em outro diretorio de colecao;
2. manter o RAW anterior;
3. reconstruir toda a SILVER;
4. reconstruir todas as GOLDs;
5. arquivar a GOLD anterior para comparacao;
6. comparar anos, linhas, classes, municipios e schema;
7. comparar indicadores no ultimo ano em comum;
8. gerar um manifest de impacto da mudanca.

## Atlas Digital De Desastres / S2ID

O Atlas responde:

> O que ja foi registrado oficialmente neste municipio?

Ele nao estima risco futuro nem probabilidade de desastre. O pipeline descobre na pagina oficial a base completa CSV e XLSX, o manual metodologico e o log de correcoes. Os quatro recursos sao preservados e seus hashes integram a identidade da carga.

Release atual:

```text
atlas_1991_2025_v1.1_2026-08-06
```

O CSV CP1252 de valores corrigidos possui 76.190 registros e 70 colunas. `Cod_IBGE_Mun` e a chave territorial; o protocolo S2ID permanece um identificador opaco. Divergencias internas do protocolo, eventos posteriores ao registro e repeticoes na chave natural sao sinalizadas, sem reescrita ou deduplicacao indevida.

O XLSX fornece 65 tipos COBRADE e os fatores de correcao IGP-DI. As medidas monetarias desta release estao corrigidas para dezembro de 2025. As flags `is_rain_related`, `is_hydrological` e `is_geological` sao documentais e versionadas; nao representam causalidade atribuida ao evento.

As GOLDs publicadas sao:

- `fact_disaster_event`, uma linha por evento oficial, preservando divergencias de matching;
- `snapshot_municipality_disaster_history`, uma linha por municipio na data de referencia;
- `municipality_disaster_type_summary`, uma linha por municipio e COBRADE;
- `municipality_disaster_month_profile`, uma linha por municipio e mes.

`dim_disaster_type` fica na SILVER, com uma linha por COBRADE oficial.

Todos os 5.256 codigos municipais observados foram associados a `dim_municipality`. As 315 unidades sem registro permanecem no snapshot com contagens zero. Isso significa somente **0 eventos encontrados na fonte**.

A metodologia, schemas, anomalias preservadas e regras de reconciliacao estao em [`atlas.md`](atlas.md) e [`atlas-data-quality-report.md`](atlas-data-quality-report.md).

## Instalacao

Requisitos:

- Python 3.11 ou superior;
- acesso HTTPS ao IBGE, MapBiomas e infraestrutura de distribuicao;
- espaco local para RAW e Parquets;
- DuckDB 1.3.2;
- extensao oficial `excel` do DuckDB para leitura do XLSX.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Dependencias Python atuais:

```text
duckdb==1.3.2
pytest==8.3.4
```

O projeto nao depende de pandas, Polars, requests, BeautifulSoup, GDAL, GeoPandas, Rasterio ou Earth Engine API.

## Execucao

### Construir A Dimensao IBGE

```bash
python -m src.pipeline
```

### Construir MapBiomas

`dim_municipality.parquet` deve existir antes da carga MapBiomas.

```bash
python -m src.mapbiomas
```

### Construir Atlas/S2ID

`dim_municipality.parquet` deve existir antes da carga Atlas.

```bash
python -m src.atlas
```

### Executar Testes

```bash
python -m pytest -q
```

Resultado atual:

```text
15 passed
```

### Execucao Completa Recomendada

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python -m pytest -q
```

Saida validada em 2 de setembro de 2026:

```text
dim_municipality criada: 5571 linhas, 27 UFs, 5 regioes.
MapBiomas colecao 11 PASS: 2798168 linhas FACT, cobertura municipal 99.982050%.
Atlas atlas_1991_2025_v1.1_2026-08-06 PASS: 76190 eventos FACT, cobertura municipal 94.345719%.
15 passed
```

## Consultas Com DuckDB

Esta secao apresenta consultas curtas. O guia completo de consumo, incluindo o
catalogo de tabelas, joins entre produtos, acesso via Python e cautelas
semanticas, esta em [`como-consumir.md`](como-consumir.md).

### Abrir Os Parquets

```python
import duckdb

connection = duckdb.connect()

municipalities = connection.read_parquet(
    "data/gold/dim_municipality.parquet"
)
snapshots = connection.read_parquet(
    "data/gold/snapshot_municipality_land_cover.parquet"
)
```

### Snapshot Mais Recente De Um Municipio

```sql
SELECT
    d.codigo_ibge,
    d.municipio,
    d.sigla_uf,
    s.year,
    s.urban_area_ha,
    s.urban_area_pct,
    s.native_vegetation_area_ha,
    s.native_vegetation_area_pct,
    s.water_area_ha,
    s.wetland_area_ha
FROM read_parquet('data/gold/snapshot_municipality_land_cover.parquet') s
JOIN read_parquet('data/gold/dim_municipality.parquet') d
    USING (codigo_ibge)
WHERE d.codigo_ibge = '3550308'
ORDER BY s.year DESC
LIMIT 1;
```

### Serie De Area Urbanizada

```sql
SELECT
    year,
    area_ha,
    area_km2
FROM read_parquet('data/gold/fact_municipality_land_cover.parquet')
WHERE codigo_ibge = '4202404'
  AND class_id = 24
ORDER BY year;
```

### Mudancas De Longo Prazo

```sql
SELECT
    d.municipio,
    d.sigla_uf,
    c.first_year,
    c.latest_year,
    c.urban_area_change_ha,
    c.urban_area_change_pct,
    c.native_vegetation_change_ha,
    c.native_vegetation_change_pct
FROM read_parquet('data/gold/municipality_land_cover_change.parquet') c
JOIN read_parquet('data/gold/dim_municipality.parquet') d
    USING (codigo_ibge)
ORDER BY c.urban_area_change_ha DESC;
```

### Municipios Em Mais De Um Bioma

```sql
SELECT
    codigo_ibge,
    list_sort(list_distinct(list(biome_name))) AS biomes
FROM read_parquet('data/silver/mapbiomas_land_cover.parquet')
GROUP BY codigo_ibge
HAVING count(DISTINCT biome_name) > 1
ORDER BY codigo_ibge;
```

### Auditoria De Matching

```sql
SELECT DISTINCT codigo_ibge
FROM read_parquet('data/silver/mapbiomas_land_cover.parquet')
WHERE NOT is_dim_municipality_match
ORDER BY codigo_ibge;
```

## Linhagem E Reprodutibilidade

### Dimensao IBGE

O manifest `data/raw/raw_ibge_municipalities_metadata.json` registra:

- endpoint;
- instante da consulta;
- status HTTP;
- headers relevantes;
- quantidade de registros;
- SHA-256 do JSON;
- SHA-256 do payload de transporte;
- campos originais observados.

### MapBiomas

Os manifests RAW registram:

- fonte e produto;
- pagina de descoberta;
- URL oficial encontrada;
- URL final resolvida;
- modo automatico ou override;
- nome original;
- status HTTP e content type;
- tamanho, ETag e Last-Modified;
- SHA-256;
- colecao e versao;
- data oficial de publicacao quando existente;
- instante de download e de ultima checagem;
- membros do ZIP;
- caminho content-addressed.

O run manifest registra:

- `run_id`;
- inicio e fim;
- colecao e versao;
- serie temporal;
- URLs e hashes;
- linhas RAW, SILVER, FACT, SNAPSHOT e CHANGE;
- cobertura municipal;
- fingerprint do pipeline;
- hashes das saidas;
- status `PASS` ou `NO_CHANGE`.

### Atlas/S2ID

O manifest Atlas registra as URLs descobertas e resolvidas, hashes de CSV, XLSX,
manual e log, release, linhas por artefato, cobertura municipal, contratos de
schema, fingerprint do pipeline e hashes das saidas. Mudancas de release geram
um relatorio de impacto e preservam os artefatos anteriores.

## Testes Automatizados

Os testes atuais cobrem:

- normalizacao de nome municipal;
- codigos administrativos como strings;
- ausencia permitida da hierarquia territorial legada;
- rejeicao quando a hierarquia territorial vigente esta ausente;
- deteccao de `codigo_ibge` duplicado;
- descoberta consistente da colecao MapBiomas;
- falha quando a colecao vigente e ambigua;
- resolucao de classes sem hardcode de IDs semanticos;
- unicidade dos snapshots materializados;
- percentuais no intervalo valido;
- presenca dos municipios de referencia;
- ausencia de infinito em indicadores percentuais de mudanca.
- descoberta inequivoca dos quatro recursos Atlas;
- rejeicao de mudanca de campos ou ordem no schema Atlas;
- classificacao de desastres relacionados a chuva por COBRADE versionado;
- idempotencia por assinatura de entrada, pipeline e artefatos;
- unicidade dos graos Atlas materializados e matching por `codigo_ibge`.

## Limitacoes Conhecidas

### Territorialidade Historica

`dim_municipality` representa o estado vigente. Ela nao resolve automaticamente codigos extintos, desmembramentos, fusoes ou mudancas historicas de codigo.

Uma futura `bridge_municipality_ibge_history` devera conter codigo de origem, codigo vigente, intervalo de validade, tipo de relacionamento, fonte legal e regras para relacoes nao 1:1.

### Data De Atualizacao IBGE

A API de Localidades nao informa versao nem data de referencia no payload. A consulta atual e rastreada por data de ingestao e hash, mas `source_updated_at` fica nulo.

### Cobertura MapBiomas

Fernando de Noronha nao aparece na tabela estatistica atual. Lagoa Mirim e Lagoa dos Patos aparecem como geocodigos da fonte, mas nao sao linhas da dimensao municipal.

### Legenda MapBiomas

O CSV de legenda e o XLSX estatistico nao possuem exatamente o mesmo conjunto de classes. A diferenca esta preservada e documentada, mas deve ser revista quando uma nova versao oficial for publicada.

### Geometrias

O projeto nao processa GeoTIFF, geometrias municipais nem raster nesta etapa. As estatisticas territoriais usadas sao as tabelas oficiais ja calculadas pelo MapBiomas.

### Semantica Dos Indicadores

Os indicadores descrevem area classificada. Nao medem diretamente impermeabilizacao, exposicao, perigo, vulnerabilidade, capacidade de drenagem ou risco.

### Registros Atlas

Os registros Atlas nao sao um inventario exaustivo de todo desastre ocorrido. O
FIDE representa o conhecimento disponivel no momento do registro, a serie
historica combina digitacao legada e S2ID, e 315 unidades da dimensao atual nao
possuem registro na release. Contagem zero descreve somente a fonte consultada.

## Proximas Etapas

Fontes candidatas para os proximos tiers:

| Fonte | Papel esperado |
|---|---|
| Indicador de Capacidade Municipal | Capacidade institucional e administrativa |
| Transferegov | Transferencias e recursos federais |
| SINISA | Saneamento e infraestrutura de servicos |
| MapBiomas tiers posteriores | Processamento espacial, somente quando necessario |

Evolucoes estruturais recomendadas:

- criar `bridge_municipality_ibge_history`;
- expandir contratos de schema versionados para as demais fontes;
- comparar automaticamente novas colecoes MapBiomas com a anterior;
- expandir testes de extracao HTTP e falhas de publicacao;
- adicionar fatos e snapshots separados para cada nova fonte;
- manter qualquer score futuro fora das tabelas de evidencia original.

## Documentacao Detalhada

| Documento | Conteudo |
|---|---|
| [`como-consumir.md`](como-consumir.md) | Guia pratico para consultar, relacionar e exportar os Parquets |
| [`schema.md`](schema.md) | Schema completo de `dim_municipality` |
| [`source-and-territorial-decisions.md`](source-and-territorial-decisions.md) | Fonte IBGE, territorialidade e historico futuro |
| [`data-quality-report.md`](data-quality-report.md) | Relatorio de qualidade da dimensao |
| [`mapbiomas.md`](mapbiomas.md) | Fonte, schema, metodologia e GOLDs MapBiomas |
| [`mapbiomas-data-quality-report.md`](mapbiomas-data-quality-report.md) | Relatorio de qualidade MapBiomas |
| [`atlas.md`](atlas.md) | Fonte, schema, metodologia e GOLDs Atlas/S2ID |
| [`atlas-data-quality-report.md`](atlas-data-quality-report.md) | Relatorio de qualidade Atlas/S2ID |

## Resumo Das Decisoes Mais Importantes

1. `codigo_ibge` e a chave territorial canonica.
2. Nomes municipais nunca substituem a chave oficial.
3. A dimensao territorial permanece relativamente estavel e sem medidas observacionais.
4. MapBiomas e modelado em fatos e snapshots temporais separados.
5. Municipio que cruza biomas tem seus componentes somados, nunca selecionados arbitrariamente.
6. Classes pai e filhas nao sao somadas simultaneamente.
7. Toda colecao MapBiomas faz parte da identidade tecnica do dado.
8. Nova colecao implica reconstrucao da serie completa.
9. RAW e evidencia imutavel e content-addressed quando aplicavel.
10. Divergencias entre fontes permanecem visiveis em relatorios de matching.
11. Area urbanizada nao e impermeabilizacao.
12. Cobertura territorial nao e score de risco.
13. Protocolo S2ID nao substitui os campos explicitos de municipio, COBRADE ou data.
14. Ausencia de registro Atlas nao significa ausencia de desastre.
15. Sazonalidade historica nao e probabilidade futura.
