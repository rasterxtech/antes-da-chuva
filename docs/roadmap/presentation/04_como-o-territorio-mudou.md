# Prompt 04 — Como o território mudou?

Implemente o bloco **Como o território mudou?**

## Fontes
```text
data/gold/snapshot_municipality_land_cover.parquet
data/gold/municipality_land_cover_change.parquet
```
Opcionalmente `data/gold/fact_municipality_land_cover.parquet`.

## Visual principal
Gráfico temporal com duas séries:
- Área urbanizada;
- Vegetação nativa.

Preferir percentual da área mapeada, com alternância `% / km²`. Não misturar unidades no mesmo eixo.

## Intervalo
Não hardcode 1985–2025; detectar `first_year` e `latest_year`.

## Cards de variação
Mostrar valor inicial, final, variação absoluta e percentual para área urbanizada e vegetação nativa.

## Janelas
Quando já disponíveis na Gold: 5, 10, 20 anos e série completa.

## Texto
Usar frases como: `Na classificação MapBiomas, a área urbanizada passou de X km² em 1985 para Y km² em 2025.`
Nunca afirmar causalidade com perda de vegetação.

## Outras classes
Mostrar pequenos indicadores de água, áreas úmidas e agropecuária abaixo do gráfico principal.

## Cautela
Exibir: `MapBiomas representa classificação de cobertura e uso da terra. Área urbanizada não equivale diretamente a superfície impermeabilizada.`

## Payload
Adicionar `land_cover.history` e `land_cover.change`.

## Entregável
Gráfico, cards before/after, seletor de período, seletor de unidade, payload leve, estados ausentes e testes de variação.
