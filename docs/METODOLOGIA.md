# Metodologia

## Propósito e limite

Antes da Chuva organiza evidências públicas por município para apoiar perguntas
antes de uma chuva. Não produz previsão, alerta em tempo real, laudo técnico,
score, ranking de risco, diagnóstico de proteção ou inferência causal. Uma
evidência ausente nunca é convertida em zero nem em prova de ausência do
fenômeno, da política ou da cobertura.

## Arquitetura implementada

```text
IBGE, Atlas e MapBiomas
          |
          v
Pipelines Python e DuckDB
          |
          v
RAW -> SILVER -> GOLD locais, ignorados pelo Git
          |
          v
scripts/export_frontend_data.py
          |
          v
metadata.json + municipal-index.json + shards por UF
          |
          v
Aplicação React: busca no índice e carrega o shard da UF selecionada
```

O navegador não lê Parquets nem executa junções. `codigo_ibge` é sempre texto
de sete dígitos e é a chave de integração. Os detalhes dos tipos e das regras de
validação estão em [CONTRATO_APRESENTACAO_V1.md](CONTRATO_APRESENTACAO_V1.md).

## Universo territorial

A dimensão canônica é a API de Localidades do IBGE. A baseline histórica
registrada em 2 de setembro de 2026 contém 5.571 unidades analíticas: 5.569
municípios stricto sensu, Brasília/DF e Fernando de Noronha/PE. Boa Esperança do
Norte/MT integra essa dimensão, mesmo ausente do universo temporal do Censo
2022. Consulte [UNIVERSO_TERRITORIAL.md](UNIVERSO_TERRITORIAL.md) para os casos
especiais e a separação entre universo vigente e referência censitária.

## Fontes e transformação

| Fonte | Uso | Caminho até a interface | Limite principal |
|---|---|---|---|
| IBGE - API de Localidades | Identidade territorial | Pipeline canônico -> `dim_municipality` -> índice v1 | A API pode mudar; a quantidade não deve ser fixada manualmente |
| Atlas Digital/S2ID | Cinco tipologias ligadas à chuva e impactos selecionados | Pipeline canônico -> GOLDs Atlas -> shards v1 | Registros administrativos podem conter lacunas e correções |
| MapBiomas | Cobertura e uso da terra, anos e variações publicados | Pipeline canônico -> GOLDs MapBiomas -> shards v1 | Área urbanizada não equivale a impermeabilização ou risco |
| Censo 2022/SIDRA 6805 | Indicador de esgotamento sanitário | Payload legado reempacotado no shard v1 | Não é indicador de risco; pipeline canônico pendente |
| Transferegov | Instrumentos federais no recorte documentado | Payload legado reempacotado no shard v1 | Não representa todo o investimento municipal; pipeline canônico pendente |
| IDAP e orientações da Defesa Civil | Próxima ação do usuário | Link externo, sem ingestão | Não é histórico municipal nem alerta emitido pela aplicação |

As URLs oficiais, a evidência de cobertura e a decisão de uso de cada fonte estão
em [FONTES_DE_DADOS.md](FONTES_DE_DADOS.md). A auditoria que originou o recorte
está em [AUDITORIA_FONTES.md](AUDITORIA_FONTES.md).

## Estados de ausência

O contrato v1 diferencia `record`, `no_record`, `no_coverage`, `not_published`
e `not_in_legacy_universe`. Por exemplo, `no_record` no Atlas significa que não
houve registro no recorte consultado; `no_coverage` no MapBiomas não é área
zero; e `not_published` no Censo não é percentual zero. A interface deve
preservar esses significados ao apresentar números ou mensagens.

## Evidência e atualização

Os manifests compactos e relatórios em `data/manifests/` e `docs/` preservam
versões, hashes, contagens e resultados da baseline de origem. Eles são
evidência histórica: não confirmam que RAW, SILVER, GOLD ou Parquets existam
neste checkout. Uma atualização completa requer acesso às fontes oficiais,
espaço local e as etapas descritas em [REPRODUCAO.md](REPRODUCAO.md).

O conjunto público v1 é uma saída revisável do exportador. Ao regenerá-lo, a
metadata deve vir dos manifests da execução e os arquivos devem ser validados
antes de uma implantação. Censo e Transferegov continuarão explícitos como
`transitional_legacy` até a entrega de pipelines oficiais.
