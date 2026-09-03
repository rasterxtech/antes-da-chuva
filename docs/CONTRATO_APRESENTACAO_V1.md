# Contrato de Apresentacao v1

O exportador `scripts/export_frontend_data.py` cria os arquivos locais abaixo.
Eles sao a unica entrada prevista para a futura troca do frontend: o navegador
nao le Parquet e nao executa joins entre fontes.

```text
app/public/data/v1/
|-- metadata.json
|-- municipal-index.json
`-- uf/
    |-- AC.json ou AC-001.json, AC-002.json, ...
    `-- ...
```

O indice e somente para busca e aponta cada codigo para o caminho real do shard
da UF. Cada shard contem o payload municipal completo, ja unido pelo exportador.
O exportador agrupa por UF e `codigo_ibge` em ordem deterministica e usa alvo de
24 MiB: se toda a UF couber, publica `UF.json`; caso contrario publica somente
`UF-001.json`, `UF-002.json` e assim por diante (nunca um `UF.json` incompleto).
Ele aborta se um payload municipal individual exceder o alvo. Todos os
`codigo_ibge` sao strings de sete digitos, inclusive chaves de objetos JSON.

As definicoes de tipos estao em `src/contracts/presentation.py` e
`app/lib/presentation-contract.ts`. Ambos usam `schema_version: "v1"` e os
mesmos estados semanticos.

## Estados semanticos

| Estado | Significado |
|---|---|
| `record` | A fonte e o recorte possuem registro. Numeros, inclusive `0`, sao valores observados. |
| `no_record` | A fonte foi consultada no recorte, mas nao devolveu registro. Nao prova ausencia do fenomeno. |
| `no_coverage` | A fonte nao cobre a unidade territorial. Nao e equivalente a zero. |
| `not_published` | A unidade existe na fonte transicional, mas o indicador nao foi publicado. |
| `not_in_legacy_universe` | A unidade vigente nao existe na referencia temporal do payload legado. |

Em particular, Fernando de Noronha tem `land_cover.state: "no_coverage"` e
Blumenau pode ter uma medida MapBiomas igual a `0` com
`land_cover.state: "record"`. Acrelandia tem `disasters.state: "no_record"`
para o recorte de chuva, embora a GOLD preserve seus outros eventos Atlas.

## Fontes canonicas e transicao

`municipality`, `disasters` e `land_cover` sao derivados exclusivamente das
GOLDs IBGE, Atlas e MapBiomas, via DuckDB. Release Atlas, colecao MapBiomas,
series e timestamps de materializacao em `metadata.json` vem dos manifests de
execucao, sem constantes de versao no frontend.

`municipality.regiao_imediata` e `municipality.codigo_regiao_imediata` preservam
a Regiao Geografica Imediata vigente do IBGE. `summary.thirty_second_text` e gerado deterministicamente pelo exportador
com os valores publicados; quando Atlas nao possui registro no recorte, seu texto
e exatamente `Nenhum registro foi encontrado nesta release do Atlas/S2ID.`.
Ausencia de cobertura MapBiomas nao gera variacao ou narrativa territorial.

`metadata.sources.atlas.catalog` e o catalogo oficial do recorte: cinco tipos
Atlas e os doze COBRADE relacionados a chuva. `disasters.history.annual` tem
primeiro/ultimo ano, serie total e por `atlas_type_id`, e benchmark da Regiao
Imediata (codigo, nome, quantidade de municipios e
`zeros_policy: "included_as_zero"`). A media inclui todos os municipios da
regiao, inclusive os sem registros no ano.

`disasters.types.event_pct` esta em 0–100; `disasters.months` sempre possui os
doze meses em ordem e usa `pct: null` quando o total e zero. Impactos humanos e
`reported_affected_total` consideram apenas eventos do recorte chuva.

`land_cover.history` preserva todos os anos da serie MapBiomas. Valores de area
sao hectares e percentuais sao 0–100; km² e somente conversao visual. A serie
inclui urbano, vegetacao nativa, agropecuaria, agua e areas umidas.
`land_cover.change` preserva anos inicial/final/referencia e as janelas GOLD de
5, 10 e 20 anos. Sem cobertura e estritamente `no_coverage`, `history: []` e
`change: null`; ausencia nunca e convertida em zero.

`census` e `transfers` sao explicitamente `provenance: "transitional_legacy"`.
Sao reempacotados do payload publicado atual para que um shard municipal nao
exija join no navegador. Eles nao sao produtos canonicos e deverao ser trocados
pelos pipelines oficiais das Fases 8 e 9. O exportador ignora completamente o
campo Atlas do payload legado.

`benchmarks.immediate_region` e calculado pelo exportador, por
`codigo_regiao_imediata`, e inclui o municipio selecionado. Possui exatamente
cinco metricas: `rain_related_event_count_10y`, `urban_change_20y_pct`,
`native_vegetation_change_20y_pct`, `urban_area_pct` e
`native_vegetation_area_pct`. Cada uma traz fonte, unidade, referencia, valor
municipal, media e mediana nao ponderadas, percentual estritamente menor e
denominador (`included`, `missing`, `undefined`). Atlas sem registro entra como
zero no denominador total; a janela rolling de dez anos declara sua
`reference_date`. MapBiomas sem cobertura e `missing`; area mapeada ou baseline
zero e `undefined`, ambos fora dos calculos. Os percentuais atuais usam o ultimo
snapshot municipal e as variacoes usam a janela de 20 anos da GOLD.

O contrato nao cria score, previsao, ranking ou inferencia causal.
