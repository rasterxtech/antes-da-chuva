# Revisão crítica de design do Antes da Chuva

Data: 08/09/2026. Estado: diagnóstico da versão anterior, preservado como referência. A execução posterior está no [registro de homologação](HOMOLOGACAO_DESIGN_STAGING.md).

## Parecer

O Antes da Chuva tem uma base visual coerente: azul-petróleo, superfícies claras e uma ilustração cartográfica que combina com o nome. A identidade, porém, enfraquece depois da abertura. O resultado municipal se torna uma sequência extensa de cartões semelhantes, com textos pequenos, títulos de pouca diferenciação e gráficos com acabamento desigual.

A melhor oportunidade é desenvolver um **atlas editorial**: uma experiência com cartografia autoral, títulos expressivos, leitura guiada e dados fáceis de comparar. O nome do produto continua Antes da Chuva; “atlas editorial” é uma direção interna de design. A marca deve ser reconhecível também no resumo, nos gráficos e no rodapé.

A crítica combinou um agente independente, encarregado da revisão do código e dos ativos, com inspeção visual e interativa da produção pelo agente principal. A habilidade `design:design-critique` orientou a análise de primeira impressão, hierarquia, consistência, usabilidade e acessibilidade. As conclusões abaixo distinguem observações da página de inferências sobre o código.

## Base e alcance da revisão

- Página observada: [antesdachuva.info](https://antesdachuva.info/).
- Código local examinado: branch `staging`, commit `062f297dae819dede873500ec250b6238dbd4daa`. Esse identificador descreve o checkout, não é uma identificação obtida do deployment público.
- Viewports observados: 1280 × 720, 390 × 844 e 320 × 740 pixels CSS.
- Estados examinados: entrada sem município, sugestões de busca, seleção por Enter, resultado de Blumenau, clique em Consultar, gráficos, fontes e rodapé.
- Dados apresentados para Blumenau: 30 registros na série histórica; 14 registros na comparação dos últimos dez anos. São recortes diferentes e precisam continuar explicitados.
- A avaliação não inclui ensaio com leitores de tela, dispositivo móvel físico, pesquisa com usuários ou medição de Core Web Vitals. Esses itens ficam no plano de homologação.

| Medição da página com Blumenau | Desktop 1280 | Mobile 390 | Mobile 320 |
| --- | ---: | ---: | ---: |
| Altura total aproximada | 7.677 px | 15.182 px | 16.387 px |
| Início do bloco de resultados | cerca de 850 px | 1.135 px | 1.212 px |
| Início do campo de busca | visível na primeira tela | 618 px | 695 px |

Altura total não é uma métrica isolada de qualidade. Aqui ela evidencia o custo da leitura linear, especialmente porque não existe navegação principal móvel. O objetivo é facilitar acesso e compreensão, preservando os dados e suas limitações.

## Achados prioritários

P1 representa um problema de uso ou interpretação a corrigir antes da homologação visual. P2 representa uma melhoria relevante de identidade, composição ou legibilidade.

| ID | Prioridade | Evidência | Consequência e recomendação |
| --- | --- | --- | --- |
| D01 | P1 | Em produção, digitar “Recife” e clicar em Consultar apagou o termo e manteve o resultado de Blumenau. `app/app/page.tsx:1199` limpa o estado da busca. | O principal botão contraria seu rótulo. Fazer o CTA consultar uma seleção válida ou apresentar as correspondências sem apagar o texto. |
| D02 | P1 | Tooltip público do histórico, no ano 2007, mostrou “Média regional” nas duas séries. `disaster-history.tsx:103` compara o nome exibido com uma chave de dados. | A pessoa não consegue identificar corretamente os valores. Usar a identidade da série e apresentar Município e Média regional de forma inequívoca. |
| D03 | P1 | A 320 px, os anos e a legenda do gráfico territorial se sobrepõem. Os pontos de 41 anos também se acumulam na pequena área de plotagem. | Ajustar ticks, margem inferior, legenda e marcadores por largura. O gráfico deve continuar legível no toque e com uma alternativa textual. |
| D04 | P1 | A navegação principal tem `display: none` a 390 px, sem alternativa no topo. `page.tsx:1065`. | Criar navegação móvel e atalhos para Resumo, Histórico, Território, Preparação e Alertas. É especialmente importante numa página tão extensa. |
| D05 | P1 | A 320 px, “Agropecuária” excede o espaço do indicador; os três indicadores territoriais ficam em colunas de aproximadamente 70 px. `land-cover-history.tsx:182`. | Empilhar ou recompor os indicadores nos menores tamanhos. Validar sobreposições internas, além de verificar rolagem horizontal da página. |
| D06 | P2 | A abertura usa uma introdução extensa; a figura tem mínimo de 560 px no desktop e 300 px no mobile. `page.tsx:1279`. | Encurtar a proposta de valor e reposicionar a arte no celular. Exibir busca e convite à demonstração cedo. |
| D07 | P2 | Cinco comparações são distribuídas em três colunas, deixando grande espaço vazio na segunda linha. Confirmado visualmente. `regional-comparison.tsx:70`. | Substituir o grupo por cinco linhas comparáveis no desktop e blocos compactos no mobile. Evitar preencher a lacuna com um indicador sem propósito. |
| D08 | P2 | Títulos principais usam Atkinson; Bricolage quase só aparece na marca. São importados Atkinson 400 e 700, mas títulos pedem 600. | Usar Bricolage nos títulos editoriais e manter Atkinson na leitura, números e controles. Alinhar os pesos usados às faces carregadas. |
| D09 | P2 | Notas, universos, instruções e legendas usam frequentemente 12 ou 14 px, apesar do corpo global de 17 px. | Estabelecer notas normalmente em 14 px e leitura em 16–18 px. Dar mais espaço a informações que explicam o número. |
| D10 | P2 | Cards dentro de cards, repetição de estatísticas e vários títulos concorrentes. O saneamento recebe mais contraste que outros temas por usar uma superfície totalmente escura. | Organizar capítulos e diferenciar resumo, análise e ação. Usar o destaque mais forte para a leitura prioritária, sem sugerir que saneamento é uma medida de risco. |
| D11 | P2 | Crescimento urbano e variação de vegetação aparecem no mesmo verde, inclusive com sinais diferentes. Gráficos usam cores próprias em vez dos tokens do projeto. | Cor deve identificar assunto ou série. Combinar cor com rótulo e traçado; não atribuir julgamento positivo ou negativo automaticamente. |
| D12 | P2 | O símbolo completo possui bastante transparência e muitos detalhes numa caixa pequena. A medição do agente estimou desenho útil de cerca de 30 px dentro da caixa de 48 px. | Preparar versão óptica compacta do símbolo para header e alinhar a família visual com o favicon; preservar a versão detalhada para usos maiores. |
| D13 | P2 | A legenda sobre a ilustração parece apagada. Há uma camada de gradiente `::after` no mesmo quadro. | Definir a ordem das camadas e contraste do texto sobre a imagem. A causa exata do efeito de escurecimento ainda exige inspeção específica durante a implementação. |
| D14 | P2 | Os painéis informativos usam hover com elevação, mesmo sem ação de clique. A imagem e parte do fundo têm movimento contínuo. | Concentrar feedback de interação em controles e links. Usar movimento ambiental discreto e respeitar redução de movimento inclusive na rolagem acionada por JavaScript. |
| D15 | P2 | A seção de fontes mostra `atlas_1991_2025_v1.1_2026-08-06` no título. No desktop, o título mediu 262 px de conteúdo para aproximadamente 239 px disponíveis. | Mostrar nome humano da base; deixar versão técnica nos detalhes. Completar links e metadados das seções novas, incluindo MapBiomas. |
| D16 | P2 | O estado vazio explica “código IBGE válido selecionado no índice publicado”. O resumo mistura `33.20 km²` com números formatados em português em outros blocos. | Trocar linguagem de implementação por orientação à pessoa e unificar a formatação, preservando precisão e significado. |

Os caminhos da tabela são relativos à raiz do repositório e as linhas correspondem ao checkout examinado.

## O que já funciona bem

**Cores.** A combinação de petróleo e papel transmite seriedade sem parecer um formulário administrativo. As medições estáticas dos tokens feitas pelo agente encontraram aproximadamente 14,83:1 entre texto principal e fundo e 6,30:1 entre texto secundário e fundo. Isso não valida todas as transparências e textos sobre imagens, mas indica que a paleta base não precisa ser substituída.

**Legibilidade de base.** Atkinson Hyperlegible continua uma escolha coerente para leitura pública. O problema atual está principalmente na escala, nos pesos e na distribuição da ênfase.

**Ilustração.** Rios, território e chuva criam uma conexão temática forte. Ela deve evoluir como parte de uma família visual, com uma composição adaptada ao celular. Por ser conceitual, não deve aparentar ser um mapa de risco do município escolhido.

**Transparência.** O produto diferencia registro, ausência, declaração municipal e alerta oficial. Esses cuidados dão credibilidade e devem continuar visíveis ao simplificar a interface.

**Acessibilidade já prevista.** Há link para pular conteúdo, foco global, busca com teclado e regras CSS para redução de movimento. A seleção de Blumenau por Enter funcionou na revisão.

## Direção de arte recomendada

| Elemento | Tratamento recomendado |
| --- | --- |
| Personalidade | Editorial, territorial e humana; o dado público apresentado como uma história verificável da cidade. |
| Paleta | Petróleo nos pontos de identidade; papel nas áreas de leitura; azul da água nos dados; verde reservado ao tema vegetação; um acento quente controlado para referências. |
| Tipografia | Bricolage em marca, abertura e títulos de capítulos. Atkinson em textos, controles, notas e números. |
| Composição | Uma entrada forte, um resumo curto e capítulos com alternância de densidade. Ritmo consistente sem encaixotar toda informação. |
| Imagens | Preservar a cartografia, revisar recorte e legibilidade; símbolo compacto e imagem de compartilhamento coerente com a nova direção. |
| Gráficos | Rótulos claros, linhas distinguíveis, unidades visíveis e mesma linguagem de tooltip e legenda. |
| Efeitos | Transições curtas nos controles e uma presença ambiental discreta. O conteúdo permanece imediatamente acessível. |
| Rodapé | Marca em superfície neutra, navegação útil, metodologia, todas as fontes efetivamente usadas e acesso ao código público. |

Outras direções consideradas foram um observatório utilitário, de maior densidade, e uma abertura imersiva de paisagem. A primeira tende a perder expressão; a segunda pode alongar ainda mais a entrada. O atlas editorial oferece a melhor continuidade com os ativos atuais.

## Concurso e prioridade

A [página oficial consultada em 08/09/2026](https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/concurso-dados-abertos) informa encerramento das inscrições em 11/09/2026, com programação sujeita a alterações. A recomendação é executar primeiro correções de uso, legibilidade, hero e composição, com homologação incremental.

Esta revisão não atribui nota oficial nem estima chance de vitória. O projeto já registra divergência entre a tabela da página-resumo e o edital em [CRITERIOS_DO_CONCURSO.md](CRITERIOS_DO_CONCURSO.md). A direção visual deve facilitar a demonstração de utilidade e confiança, sem depender de uma interpretação de pesos para justificar decisões.

O [plano de implementação e homologação](PLANO_DESIGN_STAGING.md) detalha os pacotes, os critérios de aceite e o fluxo até staging.
