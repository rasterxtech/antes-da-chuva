# Critérios e requisitos do concurso

## Fontes oficiais

- [Página do 2º Concurso de Reúso de Dados Abertos](https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/concurso-dados-abertos)
- [Edital CGU nº 46, de 19 de junho de 2026](https://www.in.gov.br/web/dou/-/edital-cgu-n-46-de-19-de-junho-de-2026-714061716)
- Contato oficial para esclarecimentos: `dadosabertos@cgu.gov.br`

## Regra que adotaremos

A página-resumo da CGU exibe uma tabela de critérios diferente da constante no Edital nº 46/2026. Para decisões de produto e pontuação, este projeto adotará o edital publicado no Diário Oficial da União e registrará a inconsistência como risco a esclarecer.

## Critérios do Edital nº 46/2026

| Critério | Peso | Descrição operacional |
|---|---:|---|
| Apresentação e usabilidade | 1 | Despertar interesse e facilitar a compreensão. |
| Inovação e originalidade | 1 | Tecnologia, conteúdo ou experiência nova que gere novas perspectivas. |
| Relevância e impacto | 2 | Dimensão e alcance do impacto potencial. |
| Benefício para sociedade ou economia | 2 | Melhorar serviços, políticas, transparência, controle social, direitos, conhecimento, inovação ou economia. |
| Replicabilidade e escalabilidade | 1 | Potencial de ampliação e replicação, código aberto e licenças adequadas. |

- Cada julgador atribui nota inteira de 0 a 10 por critério.
- Pontuação máxima ponderada: **70 pontos**.
- Desempate: benefício; impacto; inovação; apresentação; replicabilidade; por último, inscrição mais antiga.

## Mapa de evidências

Esta tabela associa cada critério a artefatos que podem ser revisados no
repositório. Ela não afirma avaliação, nota, homologação ou submissão.

| Critério | Evidência no repositório | Confirmação ainda necessária |
|---|---|---|
| Apresentação e usabilidade | `app/app/page.tsx`, `app/test/page.test.tsx`, [ACESSIBILIDADE.md](ACESSIBILIDADE.md) | Revisão manual em navegador, inclusive mobile e tecnologias assistivas |
| Inovação e originalidade | [METODOLOGIA.md](METODOLOGIA.md), [CONTRATO_APRESENTACAO_V1.md](CONTRATO_APRESENTACAO_V1.md) | Descrição final aprovada pela equipe no formulário |
| Relevância e impacto | [AUDITORIA_FONTES.md](AUDITORIA_FONTES.md), [DESCRICAO_SUBMISSAO.md](../deliverables/DESCRICAO_SUBMISSAO.md) | Texto final, público-alvo e impacto revisados pela equipe |
| Benefício para sociedade ou economia | `app/app/page.tsx`, [METODOLOGIA.md](METODOLOGIA.md), [ROTEIRO_DEMO.md](../deliverables/ROTEIRO_DEMO.md) | Demonstração e declaração final no formulário |
| Replicabilidade e escalabilidade | `src/`, `tests/`, `scripts/export_frontend_data.py`, [REPRODUCAO.md](REPRODUCAO.md), `scripts/verify_clean_clone.sh` | Executar e registrar o ensaio em clone limpo; definir licença e titular |

## Evidências de admissibilidade

| Requisito | Evidência local preparada | Estado externo |
|---|---|---|
| Uso e identificação de dados públicos | [FONTES_DE_DADOS.md](FONTES_DE_DADOS.md), [AUDITORIA_FONTES.md](AUDITORIA_FONTES.md) | Pendente de conferência no formulário |
| Metodologia e limites | [METODOLOGIA.md](METODOLOGIA.md), [CONTRATO_APRESENTACAO_V1.md](CONTRATO_APRESENTACAO_V1.md) | Pronto para referenciar; publicação e URL final pendentes |
| Código aberto e licença adequada | Código, testes e documentação no repositório | Pendente: licença e titular não foram definidos |
| Iniciativa funcional | Interface e testes de contrato no checkout | Pendente: validar implantação alvo e registrar smoke test |
| Evidência de inscrição e homologação | Estrutura em `deliverables/` | Pendente: ação e confirmação no portal |

## Admissibilidade

- Formulário submetido dentro do prazo.
- Iniciativa funcional cadastrada como caso de reúso e enviada para homologação durante o período de inscrição.
- Uso e identificação de dados públicos em formato aberto.
- Referência a pelo menos um conjunto de dados no Dados.gov.br ou em site oficial do Governo Federal.
- Iniciativa que promova direitos, transparência, controle social, melhoria de serviços ou políticas, conhecimento, inovação, economia digital ou benefício social.
- Ausência de preconceito, discriminação, desinformação, plágio ou fraude.
- Participantes e equipe em situação elegível segundo o edital.

## Checklist de submissão

- [ ] Confirmar URL estável de implantação e preencher `deliverables/SMOKE_TEST_PRODUCAO.md` com data, navegador e resultado.
- [ ] Revisar links oficiais e a data de consulta em `docs/FONTES_DE_DADOS.md`.
- [ ] Publicar ou referenciar a metodologia e as limitações aprovadas.
- [ ] Definir licença e titular, adicionar `LICENSE` e alinhar o README.
- [ ] Executar `scripts/verify_clean_clone.sh` contra um commit disponível e guardar a saída ou registro no local definido pela equipe.
- [ ] Capturar a demonstração conforme `deliverables/ROTEIRO_DEMO.md` e registrar arquivos em `deliverables/capturas/`.
- [ ] Revisar e adaptar `deliverables/DESCRICAO_SUBMISSAO.md` aos campos reais do formulário.
- [ ] Enviar o formulário do concurso.
- [ ] Cadastrar o reúso no Portal Brasileiro de Dados Abertos.
- [ ] Acionar a opção “Enviar para homologação”.
- [ ] Guardar confirmação de submissão e acompanhar a homologação.
