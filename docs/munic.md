# MUNIC 2020 - Gestão de riscos e de desastres

## Papel no produto

A MUNIC responde quais estruturas e instrumentos de gestão de riscos a prefeitura
declarou possuir em 2020. Ela não mede preparo, efetividade, atualização dos planos
ou proteção da população.

No contrato de apresentação v1, esses dados formam o bloco `municipal_capacity`.
O frontend apresenta cada resposta nominalmente, sem produzir nota ou ranking.

Fonte: [IBGE, Pesquisa de Informações Básicas Municipais - MUNIC 2020](https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-deinformacoes-basicas-municipais.html?edicao=32141).

Arquivo reproduzível: `Base_MUNIC_2020.xlsx`, aba `Gestão de riscos`, no
[FTP público do IBGE](https://ftp.ibge.gov.br/Perfil_Municipios/2020/Base_de_Dados/Base_MUNIC_2020.xlsx).

## Recorte inicial

| Conceito | Variável oficial |
|---|---|
| COMPDEC ou órgão similar | `Mgrd212`, com `Mgrd216` para “não sabe” |
| Mapeamento de risco de inundação | `Mgrd181` |
| Plano de contingência para inundação | `Mgrd184` |
| Alerta antecipado para inundação | `Mgrd186` |
| Mapeamento de risco em encostas | `Mgrd201` |
| Plano de contingência para deslizamento | `Mgrd204` |
| Alerta antecipado para deslizamento | `Mgrd206` |
| Previsão de recursos na LOA | `Mgrd225` |
| Sistema de alerta da COMPDEC | `Mgrd2213` |
| Instrumentos urbanísticos | `Mgrd171` a `Mgrd176` |

O questionário oficial é a autoridade semântica para `Mgrd201`: a pergunta trata
de mapeamento de risco em encostas. O dicionário da planilha repete, aparentemente
por engano, o rótulo de inundação usado em `Mgrd181`.

## Estados preservados

- `declared_yes`: a prefeitura marcou Sim.
- `declared_no`: a prefeitura marcou Não.
- `refused`: o município consta como Recusa.
- `not_reported`: o bloco não foi informado.
- `unknown`: a prefeitura marcou a opção Não sabe no quesito da COMPDEC.
- `not_applicable`: o quesito era condicional e aparece como `-`.
- `not_in_source`: a unidade existe na dimensão territorial atual, mas não na edição de 2020.

`not_applicable` e `not_in_source` nunca são convertidos em Não. A previsão
orçamentária e os recursos da COMPDEC são perguntados somente quando o município
declara possuir COMPDEC ou órgão similar.

## Cobertura territorial

A aba possui 5.570 códigos IBGE únicos. A GOLD usa a dimensão territorial vigente
com 5.571 unidades. Boa Esperança do Norte/MT (`5101837`), criada depois da edição,
aparece como `not_in_source`.

## Licença e atribuição

O IBGE publica o arquivo em seu repositório de downloads e o enquadra em sua
política de dados abertos, mas não foi identificada uma licença SPDX específica
anexada à edição. O manifest registra `license: unspecified` e a atribuição deve
ser: “Fonte: IBGE, Pesquisa de Informações Básicas Municipais - MUNIC 2020.”
