# Inventário de fontes de dados

Estado consolidado do código em 3 de setembro de 2026. As contagens e os status
históricos abaixo descrevem a baseline materializada na origem; manifests não
substituem os arquivos locais nem comprovam uma nova execução neste clone.

| Fonte | Papel no produto | Evidência registrada | Estado atual |
|---|---|---|---|
| [IBGE - API de Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id) | Dimensão territorial e índice de busca. | Baseline com 5.571 unidades analíticas, 27 UFs e 5 regiões. | **Canônica.** Gera `dim_municipality` e o índice v1. |
| [Atlas Digital de Desastres](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) | Histórico de ocorrências e danos de 1991-2025. | 76.190 protocolos; 5.256 municípios com algum registro; 4.708 no recorte de chuva. | **Canônica.** A apresentação vem das GOLDs Atlas. |
| [MapBiomas Brasil](https://brasil.mapbiomas.org/) | Cobertura e uso da terra municipal. | Baseline da Coleção 11, série 1985-2025; 5.570 códigos associados à dimensão. | **Canônica.** Fernando de Noronha é `no_coverage`, não zero. |
| [Censo 2022 - características dos domicílios](https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/universo-caracteristicas-dos-domicilios) | Condição estrutural dos domicílios. | Tabela 6805 com 5.570 códigos; 5.545 valores numéricos e 25 indisponíveis na baseline. | **Transicional.** O payload legado é reempacotado até existir pipeline canônico. |
| [Transferências e Parcerias da União - Transferegov](https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao) | Instrumentos federais selecionados de prevenção. | Recorte amplo: 976 instrumentos em 721 municípios; atribuição estrita: 519 em 417 municípios. | **Transicional.** O payload legado é reempacotado até existir pipeline canônico. |
| [Alertas de desastres - Anatel](https://dados.gov.br/dados/conjuntos-dados/anatel-utilidade-publica) | Histórico de mensagens de alerta por município. | Painel oficial possui filtro municipal e exportação; ingestão automática não fechada. | **Condicional.** Não integra o contrato v1. |
| [IDAP - alertas ativos](https://idap.mdr.gov.br/) | Próxima ação oficial do usuário. | Consulta pública por localidade; não é base histórica documentada para ingestão. | **Link de serviço, não fonte analítica.** |
| [Atlas da Vulnerabilidade Social - Ipea](https://dados.gov.br/dados/conjuntos-dados/ivs) | Referência conceitual de vulnerabilidade. | Base municipal publicada ligada aos Censos 2000/2010; atualização não verificável na auditoria. | **Não usar no MVP.** |
| [Índice Integrado de Seca - Cemaden](https://www.gov.br/cemaden/pt-br/assuntos/monitoramento/impactos-seca/monitoramento-de-seca-para-o-brasil/monitoramento-de-secas-e-impactos-no-brasil-2013-junho-2026/IIS_Brasil_2026_06.xlsx/view) | Monitoramento mensal de seca. | 5.570 códigos municipais; janeiro de 2021 a junho de 2026. | **Válida, fora do recorte de chuva.** |

## Caminho até a interface

IBGE, Atlas e MapBiomas são lidos pelos pipelines canônicos, materializados em
GOLDs locais e exportados pelo `scripts/export_frontend_data.py`. O navegador
recebe somente `metadata.json`, `municipal-index.json` e shards por UF do
contrato v1. Censo e Transferegov conservam `provenance: "transitional_legacy"`
até que seus pipelines oficiais sejam entregues. O contrato e os estados de
ausência estão em [CONTRATO_APRESENTACAO_V1.md](CONTRATO_APRESENTACAO_V1.md).

## Critérios de aprovação de uma fonte

- URL oficial e estável.
- Formato aberto e automatizável.
- Chave territorial compatível ou mapeável para código IBGE.
- Cobertura suficiente para a promessa apresentada.
- Dicionário de dados compreensível.
- Data de atualização conhecida.
- Limitações documentáveis.
- Licença compatível com publicação e redistribuição de derivados.

## Regras de uso

- A chave canônica será o código IBGE municipal de sete dígitos.
- “Sem registro encontrado” nunca será convertido em “não houve desastre”, “não houve investimento” ou “a cidade não alerta”.
- Contagem de alertas da Anatel representa mensagens/notificações, não pessoas alcançadas.
- Valores do Transferegov serão apresentados como instrumentos encontrados no recorte, não como gasto total municipal em prevenção. Além da chave do proponente, o objeto da proposta deve mencionar o mesmo município para que o instrumento apareça no produto.
- O Censo será consultado diretamente no SIDRA atual; o conjunto antigo do catálogo não será usado como atalho.
- Valor indisponível no Censo será exibido como indisponível, nunca convertido em zero.

Os resultados técnicos e as limitações estão detalhados em [Auditoria das fontes](AUDITORIA_FONTES.md).
