# Prompt 06 — Anos que marcaram a cidade

Implemente o bloco **Anos que marcaram a cidade**.

## Objetivo
Transformar a série histórica Atlas/S2ID em timeline curta e compreensível, destacando anos relevantes sem seleção manual.

## Fonte
```text
data/gold/fact_disaster_event.parquet
data/silver/dim_disaster_type.parquet
```

## Seleção
Selecionar deterministicamente até 5 anos:
1. maior número de registros relacionados à chuva;
2. maior número de mortes registradas;
3. maior número de desalojados/desabrigados ou afetados;
4. ocorrência relacionada à chuva mais recente;
5. primeira ocorrência relacionada à chuva registrada.

Deduplicar anos. Em empate, usar regra determinística e documentada, por exemplo priorizar o mais recente.

## Timeline
```text
2008 ●──────────── 2011 ●──────────── 2023 ●
```
Cada item deve explicar por que foi selecionado.

## Cautela
Não somar métricas humanas sobrepostas em um total artificial de vítimas. Use labels específicos: mortos, afetados, desalojados e desabrigados.

## Interação
Ao clicar, expandir tipos COBRADE, quantidade de registros e impactos disponíveis.

## Sem eventos
Mostrar mensagem explicativa em vez de timeline vazia.

## Payload
Adicionar `disasters.highlights`.

## Entregável
Algoritmo determinístico, payload, timeline, detalhe expansível e testes de seleção/deduplicação.
