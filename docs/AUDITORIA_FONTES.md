# Auditoria das fontes de dados

Atualizada em 30 de agosto de 2026.

## Resultado executivo

A promessa do MVP é tecnicamente viável com duas fontes centrais. O [Atlas Digital de Desastres](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) sustenta o histórico ligado à chuva e o [Censo 2022 no SIDRA](https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/universo-caracteristicas-dos-domicilios) sustenta uma condição estrutural comparável nos 5.570 municípios.

Anatel e Transferegov podem enriquecer a jornada, mas não devem determinar uma nota de proteção. IVS e Cemaden não entram no primeiro pipeline.

## Critérios usados

Cada fonte foi examinada quanto a:

1. acesso por URL oficial;
2. formato reutilizável;
3. granularidade e chave municipal;
4. período e atualização;
5. cobertura da promessa;
6. risco de interpretação indevida;
7. possibilidade de atualização reproduzível.

## 1. Atlas Digital de Desastres — aprovado para o núcleo

- Arquivo testado: `BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx`.
- Publicação oficial: versão 1.1, datada de 6 de agosto de 2026.
- Período: 1991–2025.
- Estrutura observada: 76.190 linhas e 76.190 protocolos S2ID únicos; nenhum código municipal ausente.
- Cobertura: 5.256 códigos municipais com algum registro de desastre.
- Recorte do MVP: 29.352 registros, em 4.708 municípios, para alagamentos, enxurradas, inundações, chuvas intensas e movimento de massa.
- Chave: `Cod_IBGE_Mun`, com sete dígitos.
- Campos úteis: protocolo, município, UF, data do evento, COBRADE, tipologia, status e danos humanos/material/econômico.

### Limites de uso

- A base reflete registros informados no S2ID; erros e incompletudes de preenchimento municipal são possíveis.
- Há registros com status “Registro” e “Reconhecido”. A interface deve nomeá-los como registros, salvo quando filtrar explicitamente o status.
- Ausência no recorte não prova ausência histórica de evento.
- Valores de danos devem receber validação adicional antes de ganhar destaque; a primeira entrega pode usar contagem, período e impactos humanos selecionados.

## 2. Censo 2022/SIDRA — aprovado para o núcleo

- Tabela testada: 6805, “Domicílios particulares permanentes ocupados por tipo de esgotamento sanitário”.
- Período: 2022.
- Granularidade: município, código IBGE de sete dígitos.
- Teste nacional da categoria total: 5.570 linhas, 5.570 códigos únicos e nenhum valor ausente.
- Medida proposta: `100% - percentual de domicílios em rede geral, rede pluvial ou fossa ligada à rede` (categoria 46290).
- Resultado da medida escolhida: 5.545 valores numéricos e 25 marcações `-` (valor não publicado). A interface preserva essa ausência como indisponível, sem imputar zero.
- Consulta de validação: [API SIDRA — total municipal](https://apisidra.ibge.gov.br/values/t/6805/n6/all/v/381/p/2022/c11558/46292?formato=json).

### Limites de uso

- É uma fotografia de 2022, não um indicador em tempo real.
- A medida descreve forma de esgotamento; não deve ser rotulada como risco de desastre nem como vulnerabilidade social total.
- O catálogo geral do Censo no Dados.gov.br está desatualizado. O pipeline deve usar a página e a API atuais do SIDRA.

## 3. Transferegov — aprovado como evidência complementar

- Repositório oficial testado: [arquivos abertos do Transferegov](https://repositorio.dados.gov.br/seges/detru/).
- Arquivos observados com data de 17 de julho de 2026.
- Recorte aplicado: programas de “Prevenção e Preparação para Desastres” e “Gestão de Riscos e Desastres” associados às ações 8172, 8865, 00TK e 00T5.
- Resultado do recorte amplo: 10.362 propostas únicas relacionadas; 976 instrumentos celebrados; 721 municípios proponentes com instrumento no recorte.
- Regra de atribuição usada no produto: o objeto da proposta deve mencionar explicitamente o mesmo município associado ao proponente. Permanecem 519 instrumentos atribuíveis a 417 municípios.
- Chave: código IBGE municipal presente na proposta.

### Limites de uso

- O recorte não representa todo o gasto municipal, estadual ou federal em prevenção.
- A maior parte das propostas relacionadas é antiga; propostas recentes são esparsas.
- Proposta não equivale a instrumento celebrado. O MVP usa somente os 519 instrumentos celebrados que também passam pela regra estrita de atribuição local e expõe situação e valores separadamente.
- Valores usam convenção decimal brasileira e exigem conversão explícita.
- Texto recomendado: “instrumentos federais encontrados neste recorte”.

## 4. Anatel — uso condicionado à reprodução da exportação

- O [painel oficial de alertas](https://informacoes.anatel.gov.br/paineis/utilidade-publica) permite filtrar por forma de entrega, data, UF e município e possui função de exportação.
- O [Defesa Civil Alerta](https://www.gov.br/anatel/pt-br/dados/utilidade-publica/alertas-de-desastres) alcançou disponibilidade nacional em 2025.
- O conjunto publicado no Dados.gov.br informa formatos ZIP/CSV e glossário, mas o endereço direto do recurso não ficou disponível por uma interface automatizável durante a auditoria.

### Limites de uso

- Os totais representam alertas/notificações, não pessoas alcançadas.
- “Nenhum alerta encontrado” não permite concluir que o município não possui capacidade de alertamento.
- O dado só entrará no MVP se a exportação puder ser repetida e documentada. Caso contrário, a aplicação apontará para o painel oficial.

## 5. IVS — não aprovado para o dado municipal do MVP

- O catálogo possui 28 recursos, mas o ZIP “Municípios - Base IVS” aparece com atualização indisponível por resposta diferente de HTTP 200.
- O recurso foi catalogado em 2019; a alteração recente do conjunto não comprova atualização da base municipal.
- A metodologia municipal publicada foi construída com variáveis dos Censos 2000 e 2010.
- Em 2025, o Ipea publicou [ajustes para futura compatibilização com o Censo 2022](https://repositorio.ipea.gov.br/entities/publication/0acfbd34-b732-4982-809e-f73e21af9d52), o que reforça que a versão municipal de 2022 não deve ser presumida pronta.

### Decisão

Usar o IVS como referência conceitual e futura fonte comparativa. No MVP, preferir uma medida direta e atual do Censo 2022, sem índice opaco.

## 6. Cemaden/IIS — fonte válida, fora do recorte

- Arquivo testado: IIS de junho de 2026.
- Estrutura: 5.570 linhas, um código IBGE único por unidade municipal e 166 colunas.
- Série: janeiro de 2021 a junho de 2026; as colunas mais recentes estavam completas.
- O valor zero encontrado em células históricas não pertence à legenda de classes 1–6 e deve ser tratado como ausente.

### Decisão

Não usar no MVP porque o indicador mede seca, enquanto a promessa inicial foi fechada em desastres ligados à chuva. A fonte fica pronta para uma expansão temática futura.

## Contrato de linguagem da interface

| Situação nos dados | Texto permitido | Texto proibido |
|---|---|---|
| Sem registro no Atlas | “Nenhum registro encontrado nas cinco tipologias entre 1991 e 2025.” | “Nunca houve desastre.” |
| Sem instrumento atribuível no recorte do Transferegov | “Nenhum instrumento federal encontrado neste recorte.” | “A cidade não investe em prevenção.” |
| Sem alerta exportado da Anatel | “Sem dado reproduzível para este recorte; consulte o painel oficial.” | “A cidade não emite alertas.” |
| Condição do Censo | “X% dos domicílios estavam fora da categoria selecionada em 2022.” | “X% da cidade está em risco.” |

## Conclusão

O MVP deve ser construído primeiro com Atlas + Censo. Transferegov entra como uma terceira camada curta e explicada. Anatel é uma melhoria de alto valor, mas não pode bloquear a entrega. Essa arquitetura preserva impacto, transparência e escalabilidade sem produzir uma conclusão mais forte que os dados.
