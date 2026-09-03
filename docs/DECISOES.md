# Registro de decisões

Decisões são registradas para evitar mudanças de direção sem evidência durante o prazo curto do concurso. As decisões D-001 a D-011 preservam o contexto do MVP inicial; as decisões posteriores registram o estado consolidado.

## D-001 — Nome

- **Decisão:** Antes da Chuva.
- **Subtítulo:** Inteligência pública para prevenir desastres.
- **Motivo:** nome humano, memorável e compatível com diferentes tipos de desastre e expansões futuras.
- **Status:** adotada em 30/08/2026.

## D-002 — Tema

- **Decisão:** prevenção de desastres e transparência da proteção civil no nível municipal.
- **Motivo:** combina relevância nacional, benefício direto, dados geográficos, orçamento, vulnerabilidade e controle social.
- **Status:** adotada em 30/08/2026; formulação específica ainda será validada pelos dados.

## D-003 — Filosofia do MVP

- **Decisão:** entregar uma resposta acionável em um minuto, em vez de um painel exploratório genérico.
- **Motivo:** a usabilidade e o benefício precisam ser perceptíveis sem conhecimento técnico.
- **Status:** adotada em 30/08/2026.

## D-004 — Uso de inteligência artificial

- **Decisão:** não usar IA para prever desastres no MVP.
- **Motivo:** prazo, risco de falsa precisão e ausência de necessidade para demonstrar valor. IA poderá ser usada posteriormente para explicação, nunca para substituir evidência.
- **Status:** adotada em 30/08/2026.

## D-005 — Promessa central

- **Decisão:** “Digite seu município e, em menos de um minuto, veja o histórico de desastres ligados à chuva, uma vulnerabilidade estrutural que pode ampliar o dano e as evidências públicas de prevenção que conseguimos comprovar — sempre com fonte e limite.”
- **Motivo:** é pequena, demonstrável com dados validados e útil sem alegar uma capacidade de diagnóstico que as fontes não sustentam.
- **Status:** adotada em 30/08/2026.

## D-006 — Recorte de desastre

- **Decisão:** o MVP usará cinco tipologias do Atlas Digital: alagamentos, enxurradas, inundações, chuvas intensas e movimento de massa, no período de 1991 a 2025.
- **Motivo:** preserva coerência com o nome Antes da Chuva e reduz a primeira versão a um problema compreensível.
- **Status:** adotada em 30/08/2026.

## D-007 — Fontes centrais e complementares

- **Decisão:** Atlas Digital e Censo 2022/SIDRA 6805 formam o núcleo obrigatório. Transferegov é complementar. Anatel entra como dado somente se a exportação municipal for reproduzível; IDAP será link de ação. Cemaden e IVS ficam fora do pipeline inicial.
- **Motivo:** separa dados com cobertura e acesso já comprovados de fontes úteis que ainda possuem limitações técnicas ou incompatibilidade temática.
- **Status:** adotada em 30/08/2026.

## D-008 — Sem nota de proteção

- **Decisão:** não criar índice composto, ranking ou resposta binária “protegida/não protegida”.
- **Motivo:** ausência de alerta ou instrumento em uma fonte não prova ausência de prevenção; somar componentes heterogêneos produziria falsa precisão.
- **Status:** adotada em 30/08/2026.

## D-009 — Escala nacional com ausência explícita

- **Decisão:** a busca cobrirá as 5.570 unidades municipais do Censo 2022. Onde o Atlas não tiver registro nas tipologias selecionadas, a interface dirá “nenhum registro encontrado no recorte de 1991–2025”.
- **Motivo:** o Censo permite cobertura nacional, enquanto o histórico do Atlas contém registros ligados à chuva para 4.708 municípios. A diferença deve aparecer como limite, não como zero de risco.
- **Status:** adotada em 30/08/2026.

## D-010 — IVS como referência, não indicador do MVP

- **Decisão:** não usar o IVS municipal publicado na primeira versão; adotar medida direta do Censo 2022.
- **Motivo:** a base municipal disponível deriva dos Censos 2000/2010, o recurso ZIP tem atualização não verificável e a compatibilização do IVS com o Censo 2022 ainda aparece como trabalho metodológico do Ipea.
- **Status:** adotada em 30/08/2026.

## D-011 — Atribuição municipal estrita no Transferegov

- **Decisão:** um instrumento só aparecerá na leitura de um município quando, além de pertencer ao recorte programático e estar celebrado, o objeto da proposta mencionar explicitamente o mesmo município associado ao proponente.
- **Motivo:** a chave municipal da proposta identifica o proponente, mas alguns objetos beneficiam outra localidade. A regra reduz falsas atribuições: dos 976 instrumentos do recorte amplo, 519 permanecem vinculados a 417 municípios.
- **Status:** adotada em 30/08/2026.

## Decisões abertas

- Hospedagem definitiva e domínio público.
- Municípios usados no roteiro final de demonstração.

## D-012 — Universo territorial de apresentação v1

- **Decisão:** a busca e os shards v1 usam as 5.571 unidades territoriais analíticas vigentes da API de Localidades do IBGE, com `codigo_ibge` textual de sete dígitos.
- **Motivo:** a dimensão vigente inclui Boa Esperança do Norte/MT (`5101837`), que não estava no universo temporal de 5.570 códigos do Censo 2022. A unidade não será removida nem preenchida com zero.
- **Status:** implementada em 03/09/2026. Detalhes em [UNIVERSO_TERRITORIAL.md](UNIVERSO_TERRITORIAL.md).

## D-013 — Fontes canônicas e transicionais no contrato v1

- **Decisão:** IBGE, Atlas e MapBiomas são exportados exclusivamente das GOLDs canônicas. Censo e Transferegov mantêm `provenance: "transitional_legacy"` até que tenham pipelines oficiais.
- **Motivo:** a separação elimina o Atlas legado como fonte da interface sem fingir que Censo e Transferegov já foram canonizados.
- **Status:** implementada em 03/09/2026. Detalhes em [CONTRATO_APRESENTACAO_V1.md](CONTRATO_APRESENTACAO_V1.md).
