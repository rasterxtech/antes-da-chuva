# Antes da Chuva v1: visão do produto

Atualizado em 8 de setembro de 2026.

## Propósito

Transformar dados públicos em uma leitura municipal compreensível e rastreável, ajudando moradores, gestores, jornalistas e organizações sociais a formular perguntas sobre desastres, território e prevenção.

> Antes da próxima chuva, conheça sua cidade.

A v1 é a edição preparada para o Concurso de Reúso de Dados Abertos da CGU 2026. O controle de inscrição e seus comprovantes estão no [checklist do concurso](CRITERIOS_DO_CONCURSO.md); nomear a versão não significa que a inscrição esteja concluída.

## Públicos

- Moradores que procuram informações sobre seu município e canais oficiais de alerta.
- Gestores e Defesa Civil local que precisam consultar evidências e seus recortes.
- Jornalistas, pesquisadores e organizações de controle social que precisam rastrear as fontes.

## Experiência da v1

1. Buscar por nome, UF ou código IBGE entre as 5.571 unidades territoriais analíticas vigentes.
2. Ler um resumo municipal com contexto e fontes.
3. Explorar os capítulos Histórico, Território e Preparação, incluindo comparação com a Região Geográfica Imediata.
4. Encontrar orientações de cadastro nos canais oficiais de alerta.
5. Consultar metodologia, períodos, cobertura e limitações.

O resumo é uma entrada rápida. O aprofundamento oferece filtros, tabelas e detalhes sem transformar diferentes indicadores em uma nota única de segurança.

## Fontes e responsabilidades

| Fonte | Evidência |
| --- | --- |
| IBGE Localidades | Identidade territorial e código de integração |
| Atlas Digital/S2ID | Registros históricos e impactos de cinco tipologias relacionadas à chuva |
| MapBiomas | Mudanças classificadas na cobertura e no uso da terra |
| MUNIC 2020 | Estruturas e instrumentos declarados pelas prefeituras |
| Censo 2022, SIDRA 6805 | Condição selecionada de esgotamento sanitário |
| Transferegov | Instrumentos federais do recorte documentado, com atribuição municipal explícita |
| Defesa Civil | Canais externos de alertas oficiais |

O [contrato v1](CONTRATO_APRESENTACAO_V1.md) distingue fontes canônicas e transicionais. A [metodologia](METODOLOGIA.md) define cada métrica; o [inventário](FONTES_DE_DADOS.md) e a [auditoria](AUDITORIA_FONTES.md) registram origem e limites.

## Limites do produto

- Não faz previsão meteorológica ou de desastres, nem emite alertas oficiais.
- Não oferece índice composto de risco, prontidão ou proteção.
- Não infere causalidade, impermeabilização ou exposição a partir de área urbanizada.
- Não trata ausência de registro ou cobertura como ausência de risco ou ação pública.
- Não comprova que estruturas declaradas em 2020 continuem operacionais.
- Não coleta cadastro próprio de moradores nem replica mensagens de alerta em tempo real.

## Qualidade e publicação

A aplicação usa Next.js, React e TypeScript. Dados públicos derivados são carregados pelo contrato v1; os pipelines Python mantêm RAW, SILVER e GOLD fora do Git.

O fluxo de entrega é `branch de trabalho → staging → main`, com revisão e checks. Produção está associada a [antesdachuva.info](https://antesdachuva.info/) e a homologação a [stg.antesdachuva.info](https://stg.antesdachuva.info/). Consulte o [fluxo de release](FLUXO_DE_RELEASE.md).

A direção visual combina cartografia conceitual, títulos editoriais e texto legível. Testes, capturas, limitações e aceite visual estão separados no [registro de homologação](HOMOLOGACAO_DESIGN_STAGING.md). Não se declara conformidade de acessibilidade ou aprovação da CGU sem a verificação correspondente.

## Material para o concurso

O produto deve demonstrar utilidade social, rastreabilidade, experiência de uso e possibilidade de reprodução. Os critérios oficiais, a divergência identificada entre página-resumo e edital e os documentos de inscrição estão em [Critérios do concurso](CRITERIOS_DO_CONCURSO.md). A meta é uma demonstração verificável, sem previsão de nota ou promessa de premiação.
