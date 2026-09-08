# Prompt 02 — O que já aconteceu?

Implemente o bloco **O que já aconteceu?**

## Objetivo
Mostrar a evolução histórica dos registros oficiais relacionados à chuva no município e contextualizar a série em relação aos municípios da mesma Região Geográfica Imediata.

## Fontes
```text
data/gold/fact_disaster_event.parquet
data/gold/dim_municipality.parquet
```
Use `is_rain_related` do pipeline Atlas.

## Visual principal
- barras: quantidade de registros relacionados à chuva por ano no município;
- linha: média anual por município da mesma Região Geográfica Imediata.

Municípios sem registro devem entrar como 0 na média quando pertencem ao universo territorial e à janela da fonte.

## Tooltip
Exemplo:
```text
2023
Blumenau: 4 registros
Média regional: 1,7
2 enxurradas
1 inundação
1 chuva intensa
```

## Cards
Mostrar total de registros, último registro, ano com mais registros, pessoas afetadas e mortes registradas.

## Filtros
Permitir, quando aplicável: todos relacionados à chuva, enxurradas, inundações, alagamentos, chuvas intensas e movimentos de massa relevantes. As opções devem vir do COBRADE existente, não de substring no frontend.

## Semântica
Subtítulo sugerido: `Registros oficiais relacionados à chuva encontrados no Atlas/S2ID.`
Explicar que a linha é a média dos municípios da mesma Região Geográfica Imediata.

## Não fazer
Não prever, projetar ou interpretar inclinação como risco crescente.

## Payload
Adicionar `disasters.history` com série municipal e benchmark regional pré-calculado.

## Entregável
Transformação, payload, gráfico, tooltips, comparação regional, estados sem dados e testes das agregações.
