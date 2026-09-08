# Prompt 01 — Resumo de 30 segundos

Implemente o primeiro bloco da página municipal do Antes da Chuva: **Resumo de 30 segundos**.

## Objetivo
Ao abrir um município, o usuário deve entender imediatamente onde está, o que já foi registrado, qual é o principal tipo de desastre relacionado à chuva, como o território mudou e qual é a referência temporal das fontes.

## Dados
Use:
```text
data/gold/dim_municipality.parquet
data/gold/snapshot_municipality_disaster_history.parquet
data/gold/municipality_disaster_type_summary.parquet
data/gold/snapshot_municipality_land_cover.parquet
data/gold/municipality_land_cover_change.parquet
```
Inspecione schemas reais antes de implementar.

## Layout
```text
BLUMENAU / SC
Região Geográfica Imediata de Blumenau

[resumo textual]

30 registros relacionados à chuva
Último registro: 2025
Área urbanizada: +XX% desde 1985
Vegetação nativa: -YY% desde 1985

Dados: Atlas/S2ID + MapBiomas
```

## Texto automático
Gerar resumo determinístico por templates, sem LLM. Exemplo:

> Desde 1991, foram encontrados 30 registros relacionados à chuva em Blumenau. Enxurradas são o tipo mais frequente na série consultada. O registro mais recente é de 2025. No território, a área classificada como urbanizada passou de X km² em 1985 para Y km² em 2025.

Não inferir causalidade.

## Ausências
Se não houver Atlas: `Nenhum registro foi encontrado nesta release do Atlas/S2ID.`
Nunca escrever `Nunca houve desastre.`
Se não houver MapBiomas, não fabricar variação.

## Roteamento
Identificar a página por `codigo_ibge`. Slug amigável é opcional, mas não substitui a chave interna.

## Payload
Criar o contrato base de payload municipal reutilizável pelos próximos blocos. Pré-calcular com Python/DuckDB e evitar joins grandes no browser.

## Entregável
1. preparação de dados;
2. contrato base do payload;
3. componente visual;
4. templates;
5. loading/error/empty states;
6. responsividade;
7. testes.

Validar Blumenau/SC, São Paulo/SP, Rio de Janeiro/RJ, Brasília/DF e município sem registro Atlas.
