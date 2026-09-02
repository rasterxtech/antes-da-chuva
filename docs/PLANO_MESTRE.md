# Plano mestre

Atualizado em 30 de agosto de 2026.

## Resultado pretendido

Entregar uma iniciativa funcional, acessível e verificável que ajude moradores, gestores, jornalistas e organizações de controle a identificar lacunas de proteção contra desastres nos municípios brasileiros.

Nosso objetivo competitivo é projetar o produto para alcançar **68 de 70 pontos**, sem depender de alegações que não possam ser demonstradas.

## Proposta de valor

> Digite seu município e, em menos de um minuto, veja o histórico de desastres ligados à chuva, uma vulnerabilidade estrutural que pode ampliar o dano e as evidências públicas de prevenção que conseguimos comprovar — sempre com fonte e limite.

Essa promessa é deliberadamente menor que um “diagnóstico de prontidão”. Os dados disponíveis não permitem afirmar de forma justa se uma cidade está ou não protegida. O produto mostrará fatos observáveis e ajudará o usuário a formular a próxima pergunta.

## Públicos prioritários

1. **Morador:** quer saber se sua família está protegida e o que fazer.
2. **Gestor ou Defesa Civil local:** precisa enxergar prioridades e justificar ações preventivas.
3. **Jornalista, pesquisador ou organização social:** quer comparar evidências e fiscalizar políticas públicas.

O MVP será desenhado primeiro para o morador. Os demais públicos receberão os mesmos dados em camadas progressivamente mais detalhadas.

## Escopo do MVP

### Obrigatório

- Busca entre as 5.570 unidades municipais do Censo 2022.
- Resumo “Sua cidade antes da próxima chuva”.
- Registros de 1991–2025 para cinco tipologias: alagamentos, enxurradas, inundações, chuvas intensas e movimento de massa.
- Uma medida estrutural do Censo 2022: percentual de domicílios sem rede geral/pluvial ou fossa ligada à rede.
- Instrumentos do Transferegov encontrados no recorte documentado de prevenção e com atribuição municipal estrita pelo objeto da proposta; alertas da Anatel somente se a exportação municipal for reproduzível a tempo.
- Linguagem explícita para “nenhum registro encontrado no recorte”, sem transformar ausência em nota negativa.
- Fonte, período, data de atualização e limitação ao lado de cada evidência.
- Link para alertas ativos no IDAP e orientações oficiais, sem prometer monitoramento em tempo real.
- Interface responsiva, acessível e utilizável em conexão lenta.
- Código e metodologia aptos à replicação.

### Fora do MVP

- Previsão meteorológica em tempo real.
- Previsão de desastre por inteligência artificial.
- Aplicativo móvel nativo.
- Cobertura perfeita de todos os tipos de desastre.
- Índice composto de risco, prontidão ou proteção.
- Comparação automática com “municípios semelhantes”.
- Mapa como experiência principal.
- Área autenticada ou cadastro de usuários.
- Denúncias, mensagens ou dados pessoais coletados pela plataforma.

## Estratégia de pontuação

| Critério oficial | Peso | Como vamos demonstrar valor |
|---|---:|---|
| Relevância e impacto | 2 | Problema nacional, experiência municipal e população vulnerável claramente identificada. |
| Benefício para sociedade ou economia | 2 | Informação acionável para prevenção, priorização de recursos e controle social. |
| Apresentação e usabilidade | 1 | Resposta em um minuto, linguagem simples, acessibilidade e detalhamento progressivo. |
| Inovação e originalidade | 1 | Conectar risco, vulnerabilidade, alertas e investimento em uma única jornada explicável. |
| Replicabilidade e escalabilidade | 1 | Pipeline automatizado, código aberto, metodologia documentada e identificador IBGE como chave nacional. |

## Cronograma

| Data | Entrega |
|---|---|
| 30/08 | Estrutura do projeto e tese inicial. |
| 31/08–01/09 | Auditoria das fontes e definição dos municípios/dados cobertos. |
| 02/09 | Especificação fechada, metodologia v1 e protótipo da experiência. |
| 03/09–06/09 | Construção do MVP e pipeline de dados. |
| 07/09 | Testes, acessibilidade, revisão metodológica e validação com usuários. |
| 08/09 | Narrativa, demonstração, imagens e documentação pública. |
| 09/09 | Cadastro do reúso e inscrição. |
| 10/09–11/09 | Margem para homologação e correções. |

## Riscos que controlaremos

| Risco | Resposta |
|---|---|
| Dados indisponíveis ou desatualizados | Validar links e granularidade antes de definir métricas. |
| Virar apenas mais um painel | Organizar a experiência em torno de perguntas e ações do usuário. |
| Escopo excessivo | Manter somente uma jornada principal e três públicos derivados. |
| Índice enganoso | Não criar índice composto no MVP; mostrar componentes observáveis e suas fontes. |
| Ausência interpretada como zero | Usar “nenhum registro encontrado no recorte” e publicar o universo consultado. |
| Perder prazo por formalidade | Finalizar em 09/09 e verificar separadamente formulário e homologação no portal. |

## Arquitetura mínima de dados

| Camada | Fonte | Papel |
|---|---|---|
| Núcleo histórico | Atlas Digital de Desastres | Registros e impactos de eventos ligados à chuva entre 1991 e 2025. |
| Núcleo estrutural | Censo 2022, SIDRA 6805 | Condição de esgotamento sanitário por município. |
| Evidência complementar | Transferegov | Instrumentos celebrados em programas e ações federais selecionados de prevenção. |
| Evidência condicional | Anatel | Histórico municipal de alertas, se o processo de exportação puder ser reproduzido. |
| Ação externa | IDAP | Consulta oficial de alertas ativos. |

Todas as junções territoriais usarão o código IBGE de sete dígitos. O detalhamento da validação está em [Auditoria das fontes](AUDITORIA_FONTES.md).

## Próximas decisões

1. Stack de implementação e hospedagem.
2. Três municípios de demonstração que cubram presença e ausência de registros.
3. Forma visual final da única página municipal.
