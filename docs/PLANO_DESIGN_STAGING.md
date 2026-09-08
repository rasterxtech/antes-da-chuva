# Plano de melhoria visual e homologação em staging

Data: 08/09/2026. Estado: núcleo implementado e validado localmente após autorização; PR e homologação de staging pendentes. Consulte o [registro de implementação e testes](HOMOLOGACAO_DESIGN_STAGING.md).

Base: [revisão crítica de design](REVISAO_DESIGN_2026-09-08.md).

## Resultado pretendido

Transformar o Antes da Chuva numa experiência editorial reconhecível, mantendo leitura acessível e rastreabilidade dos dados. A homologação acontecerá em [stg.antesdachuva.info](https://stg.antesdachuva.info/), antes de qualquer promoção para produção.

O escopo abrange header, entrada e busca, resumo, painéis municipais, gráficos, cores, tipografia, imagens, efeitos, fontes, rodapé e estados de carregamento/ausência/erro.

As regras de cálculo, recortes e contratos de dados são a referência a preservar. Se um ajuste de apresentação revelar necessidade de mudar uma regra de dados, ele deve ser explicitado e tratado separadamente. O polimento visual não exige novo backend, mapa interativo ou integração de alertas em tempo real.

## Proposta concreta de identidade

Direção: **atlas editorial**, usando a cartografia atual como identidade do produto inteiro.

### Tipografia

| Uso | Família e peso | Desktop | Mobile |
| --- | --- | --- | --- |
| Marca | Bricolage variável, 700 | Ajuste óptico ao símbolo | Preservar nome legível sem comprimir |
| Título de abertura | Bricolage, 600–700 | 48–60 px; entrelinha 1,05–1,12 | 32–38 px; entrelinha 1,1–1,18 |
| Títulos de capítulos | Bricolage, 600 | 28–36 px | 24–28 px |
| Títulos de painéis | Atkinson, 700 | 20–24 px | 20–22 px |
| Texto de leitura | Atkinson, 400 | 17–18 px; entrelinha 1,5–1,65 | 16–17 px; entrelinha 1,5–1,65 |
| Controles e notas | Atkinson, 400/700 | 14–16 px | 14–16 px |
| Valores principais | Atkinson, 700; números tabulares | 28–40 px | 26–32 px |

As duas famílias já fazem parte do projeto. Usar pesos reais disponíveis, sem introduzir outra família para leitura. Valores são faixas de projeto para validar em tela, não tamanhos fixos que impeçam reflow ou zoom. Limitar a largura de parágrafos longos a aproximadamente 60–70 caracteres.

### Paleta e componentes

| Papel | Base proposta | Aplicação |
| --- | --- | --- |
| Identidade | `--surface-storm: #17364a` | Hero, assinatura visual, ações principais e rodapé |
| Leitura | Tokens atuais de fundo e card, próximos a papel | Áreas extensas de texto e dados |
| Água e histórico | Família de `--rain-strong: #27728c` | Série municipal e elementos do tema chuva |
| Vegetação | Verde derivado do atual `#15803d` | Série vegetal, acompanhado de rótulo/traçado próprio |
| Referência regional | Acento quente a ajustar em contraste | Média/mediana regional, com forma diferente da série municipal |
| Ausência ou informação não disponível | Superfície neutra e mensagem explícita | Estado informativo, sem codificação de sucesso |

Centralizar essas funções nos tokens. A combinação teal/verde atual tem contraste de luminância de cerca de 1,05:1 entre as séries; variar traçado, marcador e identificação direta. Esse número isolado não é uma certificação de conformidade ou falha WCAG.

Adotar escala de espaçamento baseada em 4/8 px, três níveis de raio e sombras discretas. Reservar elevação por hover para componentes com ação. Um rodapé de evidência comum deve comportar fonte, período e limitação sem sobreposição.

### Entrada proposta

Copy inicial para validar:

> Antes da próxima chuva, conheça sua cidade.
>
> Veja o histórico de desastres, as mudanças no território e as evidências de preparação do seu município.
>
> Busque seu município
>
> Explorar município

Abaixo da ação, informar de forma curta: “Dados públicos com fontes, períodos e limitações visíveis”. Um atalho “Conhecer Blumenau como exemplo” pode demonstrar o produto com dados reais, com identificação explícita de exemplo.

No desktop, manter texto e ilustração em composição assimétrica equilibrada. No celular, priorizar proposta e busca; a arte pode ter uma faixa horizontal ou recorte reduzido. A intenção é deixar campo e botão inteiros acessíveis cedo, sem sacrificar tamanho de fonte.

### Organização da leitura

| Ordem | Seção | Papel |
| --- | --- | --- |
| 1 | Resumo do município | Nome, recorte, três ou quatro fatos principais e interpretação curta. |
| 2 | O que a chuva já causou | Histórico, tipos e distribuição mensal, organizados como um capítulo. |
| 3 | Como o território mudou | Uso da terra e comparação regional em composição compacta. |
| 4 | Evidências de preparação | MUNIC, saneamento e instrumentos federais, com distinção clara entre o que cada base mede. |
| 5 | Como receber alertas oficiais | Canais de ação, cadastro e orientações com hierarquia clara. |
| 6 | Como ler os dados | Metodologia e catálogo completo de fontes. |

Usar navegação por seções com o município selecionado visível. No celular, disponibilizar menu compacto acessível e retorno à busca. Qualquer comportamento fixo deve respeitar a altura útil e não cobrir conteúdo, foco ou sugestões.

Resumo e aprofundamento precisam ficar distinguíveis. Dados importantes, períodos e limitações permanecem à vista; detalhes técnicos extensos podem ir para expansões rotuladas. A comparação regional deve usar cinco linhas alinhadas no desktop, em lugar da grade de cinco cards em três colunas. Não misturar diferentes unidades em uma única escala visual.

## Pacotes de implementação

As branches abaixo registram a divisão originalmente proposta; não foram criadas. Na execução autorizada, o núcleo dos pacotes foi consolidado em `codex/design-atlas-editorial`, baseada em `origin/staging` no commit `062f297dae819dede873500ec250b6238dbd4daa`, para avaliar a composição visual em um único PR. A produção permanece fora desta entrega.

| Pacote | Branch proposta | Resultado visível | Dependência |
| --- | --- | --- | --- |
| 1. Correções de uso | `codex/design-01-usabilidade` | Consulta previsível, tooltip correto e gráficos/indicadores legíveis a 320 px | Referência visual inicial |
| 2. Identidade e entrada | `codex/design-02-identidade` | Marca presente nos títulos, hero compacto, navegação móvel e busca bem posicionada | Pacote 1 |
| 3. Leitura editorial | `codex/design-03-leitura` | Capítulos, comparação alinhada, fontes completas e hierarquia dos painéis | Pacote 2 |
| 4. Acabamento e homologação | `codex/design-04-acabamento` | Movimento, imagem de compartilhamento, ajustes finais de responsividade e evidências de validação | Pacote 3 |

### Pacote 1: correções de uso e integridade da leitura

Arquivos principais: `app/app/page.tsx`, `app/components/presentation/disaster-history.tsx`, `app/components/presentation/land-cover-history.tsx` e testes diretamente relacionados.

Trabalho:

- Fazer Consultar e Enter obedecerem à mesma regra de seleção. Texto ambíguo mantém sugestões; não escolher cidade silenciosamente nem apagar o termo.
- Corrigir tooltip para identificar Município e Média regional pela série correta.
- Explicitar se os indicadores abaixo do histórico mostram toda a série ou o tipo filtrado, preservando a definição dos dados.
- Corrigir margens/ticks/legendas no gráfico territorial em telas estreitas; reduzir marcadores sobrepostos.
- Reorganizar os três indicadores menores de território no mobile.
- Registrar capturas antes/depois dos cenários corrigidos.

Aceite: reproduzir D01–D05 da revisão, verificando correção de D01, D02, D03 e D05 neste pacote. A navegação D04 é concluída no pacote 2. Testar busca por nome e código, teclado, clique e ambiguidade; os dados de Blumenau continuam coerentes com os mesmos recortes.

### Pacote 2: identidade e primeira impressão

Arquivos principais: `app/app/globals.css`, `app/app/layout.tsx`, partes do header/hero em `app/app/page.tsx` e ativos de marca em `app/public/`.

Trabalho:

- Aplicar escala tipográfica e cores por função, usando as famílias existentes.
- Recompor o hero com copy curta, campo proeminente e recorte de imagem próprio para mobile.
- Ajustar o símbolo para renderização pequena e preservar o fundo neutro da marca no rodapé.
- Corrigir contraste e ordem das camadas da legenda sobre a ilustração.
- Implementar navegação mobile com foco controlado, fechamento por Escape e retorno ao acionador.
- Distinguir estados de carregamento, nenhuma seleção, nenhum resultado e erro com mensagens orientadas à pessoa.

Aceite: header, hero e resumo aparentam pertencer à mesma marca; a 390 × 844 o campo e a ação principal ficam inteiros na primeira tela; a 320 px o usuário chega à ação sem passar pela ilustração. Títulos não cortam e notas continuam legíveis. Você valida a direção de arte neste ponto, antes da recomposição mais ampla.

### Pacote 3: capítulos, gráficos e evidências

Arquivos principais: `app/app/page.tsx`, componentes em `app/components/presentation/` e estilos compartilhados de apresentação.

Trabalho:

- Reorganizar o resultado conforme os capítulos propostos, removendo repetições de apresentação.
- Criar a comparação regional em linhas no desktop e versão compacta no mobile.
- Padronizar legendas, eixos, tooltips, notas e controles dos gráficos; usar sinais visuais além da cor.
- Manter números, unidade e período juntos. Unificar decimais em português, verificando se a origem é texto pré-gerado antes de alterá-lo.
- Dar tratamento coerente a capacidade municipal, saneamento e instrumentos federais, sem transformar nenhum deles em nota de segurança.
- Completar fontes de histórico e território. Adicionar MapBiomas ao catálogo e ao rodapé com o recurso exato usado pelo projeto.
- Substituir identificadores técnicos nos títulos por nomes humanos; manter a versão completa nos detalhes.
- Estruturar footer com marca, navegação, metodologia, fontes e link do repositório público.

Aceite: todas as métricas mantêm significado e proveniência; não sobra a lacuna da grade regional; cada capítulo tem uma pergunta e uma conclusão legível; fontes e notas não se sobrepõem; zero, ausência e falta de cobertura seguem visualmente distintos.

### Pacote 4: imagem, movimento e validação final

Trabalho:

- Aplicar transições de aproximadamente 160–220 ms em controles e foco; transições de entrada, se usadas, discretas e sem esconder conteúdo dependente de JavaScript.
- Remover elevação de painéis estáticos e revisar movimento contínuo da imagem/fundo, com tratamento de redução de movimento também no JavaScript.
- Revisar tamanho de arquivos, dimensões e carregamento das imagens. Usar a ilustração já existente como primeiro caminho; eventual nova arte deve seguir o mesmo briefing e ser validada antes de substituir a atual.
- Alinhar favicon, símbolo, marca e imagem de compartilhamento. Não usar texto importante embutido na arte do hero.
- Executar a matriz de homologação, registrar deployment e commit e corrigir regressões observadas.

Aceite: aplicação funcional com redução de movimento; nenhum conteúdo cortado nos tamanhos previstos; experiência consistente por mouse, toque e teclado; desempenho comparado com a referência; você valida o deployment final de staging.

## Ordem de prioridade para o concurso

A [programação oficial consultada em 08/09](https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/concurso-dados-abertos) informa encerramento das inscrições em 11/09/2026. Sequência recomendada:

1. Núcleo obrigatório: defeitos de busca e tooltip, reflow dos gráficos, navegação mobile, tipografia/hero e fontes completas.
2. Ganho editorial seguinte: comparação regional, capítulos, escala de notas e redução de repetições.
3. Acabamento adicional: nova arte, animações de entrada e compartilhamento visual refinado, conforme tempo disponível após homologação do núcleo.

Essa é uma ordem de corte de escopo, não uma promessa de prazo nem confirmação de inscrição. Cada pacote precisa poder chegar funcional à homologação.

## Fluxo até staging

Seguir [FLUXO_DE_RELEASE.md](FLUXO_DE_RELEASE.md) e [CONTRIBUTING.md](../CONTRIBUTING.md).

1. Atualizar referências do GitHub e registrar o commit-base da `staging`. Verificar PRs e mudanças dos colaboradores nos arquivos afetados.
2. Criar branch `codex/…` a partir dessa base. Implementar o pacote e validar localmente.
3. Abrir PR para `staging` com propósito, capturas antes/depois, testes e mudanças de apresentação. Aguardar verificações e revisão previstas no repositório.
4. Integrar o pacote na `staging` e acompanhar seu deployment Vercel. Conferir que o domínio STG resolve para a branch e commit corretos. Manter o mecanismo de acesso já configurado para homologação.
5. Entregar a você o link de STG, o deployment específico e um roteiro curto do que mudou. Registrar seu feedback e corrigir por PR para `staging`.
6. Após homologação final, preparar a promoção `staging → main` conforme o fluxo do projeto. A revisão atual não executa essa promoção.

As proteções de revisão permanecem parte do fluxo. A equipe deve revalidar o candidato se outro PR mudar a staging depois do aceite visual.

## Matriz de homologação

| Área | Cenários | Critério de aceite |
| --- | --- | --- |
| Busca | Nome, UF, código, nomes semelhantes, nenhum resultado; mouse e teclado | Nenhuma perda involuntária do termo; resultado corresponde à seleção; dropdown e foco visíveis. |
| Município | Blumenau como caso confirmado; selecionar na base casos com poucos/nenhum registro e ausência de cobertura | Estados corretos, sem transformar ausência em zero. Os outros municípios serão escolhidos após conferir os dados. |
| Histórico | Todas as tipologias, filtro específico, tooltip em ano zero e com eventos | Rótulos corretos e contexto do filtro explícito. |
| Território | Percentual/km², série completa e períodos menores | Valores e recortes preservados; eixos, legendas e unidades legíveis. |
| Responsividade | Larguras 320, 390, 768, 1024, 1280 e 1440 px; orientação paisagem | Sem sobreposição, corte de controles ou scroll horizontal indevido; navegação disponível. |
| Legibilidade | Zoom 200%; reflow a 320 px; textos sobre imagens | Conteúdo e ações acessíveis; notas normalmente ≥14 px; contraste validado na composição efetiva. |
| Acessibilidade | Tab, Shift+Tab, Enter, Escape, foco no menu e consulta; redução de movimento | Ordem compreensível, foco não encoberto e funções principais operáveis. Complementar com leitor de tela. |
| Fontes | Cada dado, bloco, catálogo e footer | Fonte correta, período presente e versão técnica acessível sem dominar o título. |
| Assets | Símbolo pequeno, favicon 16/32 px, hero desktop/mobile, imagem de compartilhamento | Família visual consistente; nenhuma interpretação da ilustração como mapa real do município. |
| Desempenho | Mesmos cenários antes/depois, três execuções por perfil de teste | Registrar LCP/CLS, payload e mediana; investigar regressão reproduzível, especialmente por imagens e efeitos. |
| Entrega | Deployment de STG, commit, PR e responsável pela validação | Evidência do candidato testado; retorno à versão anterior identificado caso necessário. |

Para contraste, adotar pelo menos 4,5:1 em texto comum e 3:1 em texto grande, conforme [WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Para reflow, usar [WCAG 1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html). Esta matriz é critério de projeto; a execução deve registrar resultados reais, não presumir conformidade pela existência do checklist.

Verificações de código previstas pelo repositório: na raiz, `node --test .github/scripts/check-pr-target.test.cjs`; em `app`, `npm run lint`, `npm test` e `npm run build`. Adicionar testes de regressão úteis para busca e identificação de séries. Alteração de exportação/contrato exige os testes de dados descritos em CONTRIBUTING; mudanças puramente visuais não justificam recalcular as bases.

## Registro para seu aceite em STG

Preencher ao executar cada pacote:

- Pacote e PR:
- Commit validado:
- URL do deployment e domínio de STG:
- Mudanças visíveis:
- Capturas antes/depois em desktop e mobile:
- Cenários executados e resultados:
- Pendências conhecidas:
- Feedback e aceite do responsável:

O próximo passo é revisar o PR consolidado para `staging` e validar a direção de arte no deployment correspondente. Nova arte de compartilhamento e medições comparativas de desempenho continuam como acabamento adicional, sem alegação de conclusão. A homologação precede qualquer promoção para produção.
