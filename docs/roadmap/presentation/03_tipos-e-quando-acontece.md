# Prompt 03 — Tipos + Quando acontece?

Implemente dois cards irmãos:
1. **Que tipo de evento aparece mais?**
2. **Em que época aparecem mais registros?**

## Fontes
```text
data/gold/municipality_disaster_type_summary.parquet
data/gold/municipality_disaster_month_profile.parquet
data/silver/dim_disaster_type.parquet
```

## Card A — Tipos
Barras horizontais ordenadas com contagem e percentual dos eventos relacionados à chuva.

Exemplo:
```text
Enxurrada           █████████████ 13
Chuvas intensas     █████████      9
Inundação           ██████         6
Movimento de massa  ██             2
```

Gerar frase determinística, por exemplo: `Enxurradas representam 43% dos registros relacionados à chuva encontrados para o município.`

## Card B — Quando acontece?
12 barras, uma por mês. Mostrar contagem histórica e percentual opcional.

Gerar frase determinística como: `Os meses de dezembro, janeiro e fevereiro concentram 61% dos registros da série.`

Não chamar isso de época de maior risco; usar concentração histórica de registros.

## Sem dados
Se total = 0, mostrar mensagem explicativa em vez de gráfico zerado.

## Acessibilidade
Não depender só de cor; usar labels e valores.

## Payload
Adicionar `disasters.types` e `disasters.months`.

## Entregável
Dois componentes, payload, testes de porcentagem, ordenação e universo correto de eventos.
