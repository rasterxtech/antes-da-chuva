# Prompt 05 — Como este município se compara à região?

Implemente o bloco **Como este município se compara à região?**

## Objetivo
Dar contexto aos números isolados do município usando a Região Geográfica Imediata como universo principal.

## Fontes
```text
dim_municipality
snapshot_municipality_disaster_history
municipality_land_cover_change
snapshot_municipality_land_cover
```
Use os paths reais do projeto.

## Métricas iniciais
1. registros relacionados à chuva nos últimos 10 anos;
2. crescimento da área urbanizada em 20 anos;
3. variação da vegetação nativa em 20 anos;
4. percentual atual de área urbanizada;
5. percentual atual de vegetação nativa.

## Visual
Exemplo:
```text
Município    █████████████  12
Região       ─────────      7,2
```

## Benchmark
Calcular pelo menos média dos municípios da Região Geográfica Imediata. Avaliar mediana e, se houver outliers fortes, mostrar mediana ou ambos. Documentar a decisão.

## Percentil
Opcional: `Maior que 82% dos municípios da mesma região.`
Prefira percentil a ranking ordinal.

## Universo
Mostrar explicitamente quantos municípios entram na comparação.

## Missing
Para Atlas, município sem registro = 0 registros encontrados. Para MapBiomas, ausência real = missing e deve sair do denominador com disclosure.

## Não fazer
Não criar score e não usar linguagem como `mais vulnerável que a região`.

## Performance
Pré-calcular benchmarks com DuckDB durante o build. Não calcular sobre milhões de registros no browser.

## Payload
Adicionar `benchmarks`.

## Entregável
Camada de benchmark reutilizável, média, mediana, percentil, tamanho do universo, missing, componente visual e testes.
