# Universo Territorial de Apresentacao

## Referencia vigente

O indice de apresentacao v1 usa `dim_municipality`, a dimensao derivada da API
de Localidades do IBGE consultada em 2 de setembro de 2026. Ela possui **5.571
unidades territoriais analiticas**, sempre identificadas por `codigo_ibge` como
texto de sete digitos.

O total e composto por 5.569 municipios stricto sensu, Brasilia/DF como distrito
federal (`5300108`) e Fernando de Noronha/PE como distrito estadual (`2605459`).
Essa e a referencia territorial vigente do produto, nao uma recontagem do Censo.

Boa Esperanca do Norte/MT (`5101837`) faz parte dessa dimensao. Ela e mantida no
indice e recebe shard de MT mesmo quando uma fonte anterior nao a contem.

## Referencia Censo 2022

O payload publicado legado, derivado da tabela SIDRA 6805 do Censo 2022, possui
**5.570** codigos e nao contem `5101837`. Portanto, o Censo 2022 nao pode ser
tratado como a dimensao territorial vigente nem receber preenchimento por zero.

Enquanto o pipeline canonico do Censo nao existe, o exportador v1 reempacota
somente os campos legados `census` e declara uma das situacoes abaixo:

| Situacao | Significado |
|---|---|
| `record` | O indicador legado contem valor publicado; zero, se houver, continua sendo valor observado. |
| `not_published` | O municipio consta no Censo legado, mas o indicador nao foi publicado. |
| `not_in_legacy_universe` | O municipio vigente nao existe no payload legado, como Boa Esperanca do Norte. |

Nenhuma dessas situacoes mede ausencia de saneamento, risco ou cobertura de
qualquer outra fonte.

## Cobertura por fonte

Atlas e IBGE sao exportados para as 5.571 unidades a partir das GOLDs. No Atlas,
`no_record` significa que nao houve registro no recorte de cinco tipologias
relacionadas a chuva, e nao que nao houve desastre. MapBiomas Colecao 11 cobre
5.570 unidades da dimensao; Fernando de Noronha recebe `no_coverage`, jamais
zero. Os dois geocodigos adicionais do MapBiomas (Lagoa Mirim e Lagoa dos Patos)
nao pertencem a `dim_municipality` e nao entram no indice.
