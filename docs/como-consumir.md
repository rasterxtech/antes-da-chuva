# Como Consumir Os Dados

> **Disponibilidade no repositório consolidado:** os Parquets não são
> versionados. Este guia descreve a consulta após a materialização local; em um
> clone sem `data/raw/`, `data/silver/` e `data/gold/`, as consultas abaixo e os
> testes de saídas materializadas ficam bloqueados. Os manifests em
> `data/manifests/` são evidência compacta de execuções anteriores, não dados de
> consulta.

Este guia descreve como usar os artefatos materializados pelo projeto sem
executar novamente as extracoes. O produto e distribuido como arquivos Parquet;
nao existe uma API ou um banco persistente para consulta.

Todos os exemplos partem da raiz do repositorio.

## Pre-requisitos

Para consultar com Python e DuckDB:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Os arquivos em `data/gold/` precisam existir. Caso ainda nao tenham sido
materializados, execute:

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
```

A ordem e obrigatoria porque MapBiomas e Atlas usam `dim_municipality` como
referencia territorial.

## Qual Camada Usar

| Camada | Uso recomendado |
|---|---|
| `data/gold/` | Consultas analiticas, indicadores e integracao entre produtos |
| `data/silver/` | Auditoria, dimensoes auxiliares e investigacao de divergencias |
| `data/raw/` | Evidencia original, reproducao da carga e inspecao da fonte |
| `data/manifests/` | Versao, hashes, status e linhagem de cada execucao |

Comece pela GOLD. Use SILVER somente quando a pergunta exigir detalhes que foram
intencionalmente removidos ou consolidados na camada analitica.

## Catalogo Para Consumo

| Arquivo | Grao | Chave logica | Uso principal |
|---|---|---|---|
| `data/gold/dim_municipality.parquet` | Uma unidade territorial municipal vigente | `codigo_ibge` | Nome, UF, regiao e hierarquia territorial |
| `data/gold/fact_municipality_land_cover.parquet` | Municipio x ano x classe | `codigo_ibge + year + class_id` | Series detalhadas por classe MapBiomas |
| `data/gold/snapshot_municipality_land_cover.parquet` | Municipio x ano | `codigo_ibge + year` | Indicadores anuais prontos de cobertura da terra |
| `data/gold/municipality_land_cover_change.parquet` | Municipio | `codigo_ibge` | Mudancas entre anos e janelas de 5, 10 e 20 anos |
| `data/gold/fact_disaster_event.parquet` | Registro oficial de desastre | `disaster_event_id` | Eventos, impactos humanos e perdas reportadas |
| `data/gold/snapshot_municipality_disaster_history.parquet` | Municipio x data de referencia | `codigo_ibge + reference_date` | Historico acumulado e janelas recentes |
| `data/gold/municipality_disaster_type_summary.parquet` | Municipio x COBRADE | `codigo_ibge + cobrade_code` | Totais historicos por tipo de desastre |
| `data/gold/municipality_disaster_month_profile.parquet` | Municipio x mes | `codigo_ibge + month` | Perfil sazonal historico |
| `data/silver/dim_disaster_type.parquet` | Tipo COBRADE | `cobrade_code` | Nome e classificacao dos tipos de desastre |
| `data/silver/mapbiomas_class_legend.parquet` | Colecao x classe MapBiomas | `collection_id + class_id` | Legenda, hierarquia e regras das classes |

Os schemas completos estao em `schema.md`, `mapbiomas.md` e `atlas.md`.

## Relacionamentos

```text
dim_municipality.codigo_ibge
|
|-- fact_municipality_land_cover.codigo_ibge
|-- snapshot_municipality_land_cover.codigo_ibge
|-- municipality_land_cover_change.codigo_ibge
|-- fact_disaster_event.codigo_ibge
|-- snapshot_municipality_disaster_history.codigo_ibge
|-- municipality_disaster_type_summary.codigo_ibge
`-- municipality_disaster_month_profile.codigo_ibge

municipality_disaster_type_summary.cobrade_code
`-- dim_disaster_type.cobrade_code
```

Use sempre `codigo_ibge` como `VARCHAR`. Nome de municipio serve para exibicao e
busca auxiliar, nunca como chave de integracao.

## Primeira Consulta Com DuckDB

O DuckDB le os Parquets diretamente, sem importar os dados para outro banco:

```python
import duckdb

connection = duckdb.connect()

rows = connection.execute(
    """
    SELECT codigo_ibge, municipio, sigla_uf
    FROM read_parquet('data/gold/dim_municipality.parquet')
    WHERE sigla_uf = ?
    ORDER BY municipio
    LIMIT 10
    """,
    ["SC"],
).fetchall()

for row in rows:
    print(row)

connection.close()
```

Filtros e selecao de colunas sao aplicados pelo DuckDB durante a leitura. Evite
carregar um Parquet inteiro em memoria quando a consulta precisa de poucas
colunas ou municipios.

## Perfil Integrado De Um Municipio

Esta consulta combina o ultimo ano MapBiomas com o snapshot historico do Atlas.
Os `LEFT JOIN` mantem o municipio mesmo quando uma fonte nao possui observacao.

```sql
WITH latest_land_cover AS (
    SELECT *
    FROM read_parquet(
        'data/gold/snapshot_municipality_land_cover.parquet'
    )
    WHERE year = (
        SELECT max(year)
        FROM read_parquet(
            'data/gold/snapshot_municipality_land_cover.parquet'
        )
    )
)
SELECT
    d.codigo_ibge,
    d.municipio,
    d.sigla_uf,
    l.year AS land_cover_year,
    l.urban_area_pct,
    l.native_vegetation_area_pct,
    l.water_area_pct,
    a.reference_date AS disaster_reference_date,
    a.event_count,
    a.rain_related_event_count,
    a.event_count_10y,
    a.reported_affected_total
FROM read_parquet('data/gold/dim_municipality.parquet') d
LEFT JOIN latest_land_cover l USING (codigo_ibge)
LEFT JOIN read_parquet(
    'data/gold/snapshot_municipality_disaster_history.parquet'
) a USING (codigo_ibge)
WHERE d.codigo_ibge = '3550308';
```

## Serie Anual De Cobertura Da Terra

Use o snapshot para indicadores prontos e a FACT quando precisar de uma classe
especifica.

```sql
SELECT
    year,
    urban_area_ha,
    urban_area_pct,
    native_vegetation_area_ha,
    water_area_ha
FROM read_parquet(
    'data/gold/snapshot_municipality_land_cover.parquet'
)
WHERE codigo_ibge = '4202404'
ORDER BY year;
```

Consulta de uma classe MapBiomas, neste exemplo Area Urbanizada (`class_id=24`):

```sql
SELECT year, class_id, class_name, area_ha, area_km2
FROM read_parquet('data/gold/fact_municipality_land_cover.parquet')
WHERE codigo_ibge = '4202404'
  AND class_id = 24
ORDER BY year;
```

## Desastres Por Tipo

O resumo por tipo contem o codigo COBRADE. Relacione-o a
`dim_disaster_type.parquet` para obter os nomes e classificacoes.

```sql
SELECT
    d.municipio,
    d.sigla_uf,
    s.cobrade_code,
    t.disaster_name,
    t.is_rain_related,
    s.event_count,
    s.first_event_date,
    s.latest_event_date,
    s.reported_affected_total
FROM read_parquet(
    'data/gold/municipality_disaster_type_summary.parquet'
) s
JOIN read_parquet('data/gold/dim_municipality.parquet') d
    USING (codigo_ibge)
LEFT JOIN read_parquet('data/silver/dim_disaster_type.parquet') t
    USING (cobrade_code)
WHERE s.codigo_ibge = '3304557'
ORDER BY s.event_count DESC, s.cobrade_code;
```

Para analisar cada registro oficial, use `fact_disaster_event.parquet`:

```sql
SELECT
    event_year,
    count(*) AS event_count,
    sum(deaths) AS deaths,
    sum(reported_affected_total) AS reported_affected_total
FROM read_parquet('data/gold/fact_disaster_event.parquet')
WHERE codigo_ibge = '3304557'
GROUP BY event_year
ORDER BY event_year;
```

## Perfil Mensal Historico

Todos os municipios possuem 12 linhas, inclusive quando as contagens sao zero.

```sql
SELECT month, event_count, rain_related_event_count
FROM read_parquet(
    'data/gold/municipality_disaster_month_profile.parquet'
)
WHERE codigo_ibge = '3550308'
ORDER BY month;
```

## Exportar Um Recorte

O DuckDB pode gerar um CSV menor sem criar uma copia integral dos dados:

```sql
COPY (
    SELECT d.municipio, d.sigla_uf, s.* EXCLUDE (codigo_ibge)
    FROM read_parquet(
        'data/gold/snapshot_municipality_land_cover.parquet'
    ) s
    JOIN read_parquet('data/gold/dim_municipality.parquet') d
        USING (codigo_ibge)
    WHERE s.year = 2025
) TO 'snapshot_land_cover_2025.csv' (HEADER, DELIMITER ',');
```

O arquivo exportado e derivado. A fonte de verdade continua sendo o Parquet e
seus manifests.

## Validar Antes De Consumir

Confira o campo `status` destes relatorios:

| Produto | Relatorio obrigatorio |
|---|---|
| Dimensao IBGE | `data/gold/data_quality_report.json` |
| MapBiomas | `data/gold/mapbiomas_data_quality_report.json` |
| Atlas/S2ID | `data/gold/atlas_data_quality_report.json` |

O valor esperado e `PASS`. Para identificar exatamente a carga consumida,
registre tambem:

- `data/manifests/mapbiomas/latest_successful_run.json`;
- `data/manifests/atlas/latest_successful_run.json`;
- `collection_id`, `collection_version`, `source_release` e `source_sha256` das
  tabelas consultadas.

Uma execucao sem mudanca pode ter status `NO_CHANGE` no run manifest; o relatorio
de qualidade materializado continua precisando estar em `PASS`.

## Regras De Consumo

1. Trate `codigo_ibge`, `codigo_uf_ibge`, `cobrade_code` e outros codigos como
   texto. Converter para numero pode remover zeros e quebrar relacionamentos.
2. Preserve o grao de cada tabela. Juntar eventos de desastre diretamente a
   snapshots anuais multiplica linhas; agregue cada lado antes do join.
3. Parta de `dim_municipality` com `LEFT JOIN` quando precisar manter todos os
   municipios, inclusive os que nao possuem observacao em uma fonte.
4. No snapshot Atlas, zero significa nenhum registro encontrado na release, nao
   ausencia comprovada de desastre.
5. A falta de linha MapBiomas e diferente de area zero. Fernando de Noronha nao
   possui observacao na tabela municipal atual.
6. Percentuais de cobertura selecionados nao precisam somar 100%. Algumas
   categorias, como areas umidas, tambem pertencem a agregacoes mais amplas.
7. `urban_area` descreve classificacao de cobertura da terra; nao equivale a
   impermeabilizacao, exposicao ou risco.
8. `is_rain_related`, `is_hydrological` e `is_geological` sao classificacoes
   documentais versionadas, nao atribuicoes de causalidade.
9. Valores monetarios Atlas da release atual foram corrigidos por IGP-DI para
   dezembro de 2025. Preserve `monetary_reference_year` em extracoes de eventos.
10. Selecione colunas pelo nome. Nao dependa da ordem fisica nem use `SELECT *`
    em contratos externos que precisem permanecer estaveis.

## Referencias

| Documento | Conteudo |
|---|---|
| `schema.md` | Schema territorial completo |
| `mapbiomas.md` | Schemas, classes e metodologia MapBiomas |
| `atlas.md` | Schemas, COBRADE, impactos e metodologia Atlas |
| `mapbiomas-data-quality-report.md` | Validacoes da carga MapBiomas |
| `atlas-data-quality-report.md` | Validacoes da carga Atlas/S2ID |
