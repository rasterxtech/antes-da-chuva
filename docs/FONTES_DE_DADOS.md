# Inventário de fontes de dados

Atualizado em 30 de agosto de 2026. A classificação abaixo já incorpora testes de acesso, estrutura, cobertura e possibilidade de união municipal.

| Fonte | Papel no produto | Cobertura validada | Decisão |
|---|---|---|---|
| [Atlas Digital de Desastres](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) | Histórico de ocorrências e danos de 1991–2025. | 76.190 protocolos; 5.256 municípios com algum registro; 4.708 no recorte de chuva. | **Núcleo aprovado.** |
| [Censo 2022 — características dos domicílios](https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/universo-caracteristicas-dos-domicilios) | Condição estrutural dos domicílios. | Tabela 6805 testada em 5.570 municípios; a medida escolhida tem 5.545 valores numéricos e 25 indisponíveis. | **Núcleo aprovado.** |
| [Transferências e Parcerias da União — Transferegov](https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao) | Instrumentos federais selecionados de prevenção. | O recorte amplo contém 976 instrumentos em 721 municípios; a atribuição local estrita usada no produto retém 519 instrumentos em 417 municípios. | **Complementar aprovada, com ressalvas.** |
| [Alertas de desastres — Anatel](https://dados.gov.br/dados/conjuntos-dados/anatel-utilidade-publica) | Histórico de mensagens de alerta por município. | Painel oficial possui filtro municipal e exportação; ingestão automática ainda não fechada. | **Condicional.** |
| [IDAP — alertas ativos](https://idap.mdr.gov.br/) | Próxima ação oficial do usuário. | Consulta pública por localidade; não é uma base histórica documentada para ingestão. | **Link de serviço, não fonte analítica.** |
| [Atlas da Vulnerabilidade Social — Ipea](https://dados.gov.br/dados/conjuntos-dados/ivs) | Referência conceitual de vulnerabilidade. | Base municipal publicada ligada aos Censos 2000/2010; ZIP com atualização não verificável. | **Não usar no MVP.** |
| [Índice Integrado de Seca — Cemaden](https://www.gov.br/cemaden/pt-br/assuntos/monitoramento/impactos-seca/monitoramento-de-seca-para-o-brasil/monitoramento-de-secas-e-impactos-no-brasil-2013-junho-2026/IIS_Brasil_2026_06.xlsx/view) | Monitoramento mensal de seca. | 5.570 códigos municipais; janeiro de 2021 a junho de 2026. | **Válida, mas fora do recorte de chuva.** |

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
