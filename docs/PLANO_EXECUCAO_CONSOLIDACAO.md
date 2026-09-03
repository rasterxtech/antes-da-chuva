# Plano de Execução da Consolidação

Atualizado em 2 de setembro de 2026.

## Objetivo

Consolidar o produto de dados existente em
`/home/Leoni.Leopoldino/Documentos/personal/antesdachuva` no repositório Git
`/home/Leoni.Leopoldino/Documentos/personal/antes-da-chuva`, preservando o MVP
web publicado e estabelecendo uma única fonte de verdade para dados, aplicação,
testes e documentação.

A prioridade imediata é a entrega para o 2º Concurso de Reúso de Dados Abertos
da CGU. A consolidação deve ocorrer em partes pequenas, verificáveis e
reversíveis, sem interromper o funcionamento atual do site.

## Diagnóstico

- `antesdachuva` é o produto de dados mais robusto: Python, DuckDB, camadas
  RAW/SILVER/GOLD, manifests, linhagem, relatórios de qualidade e 15 testes.
- `antes-da-chuva` é o produto web: React, TypeScript, Cloudflare, identidade
  visual, narrativa e experiência municipal publicada.
- Os dois projetos processam o mesmo Atlas/S2ID com implementações diferentes.
- O frontend usa 5.570 unidades do Censo 2022; a dimensão territorial vigente
  possui 5.571, incluindo Boa Esperança do Norte/MT.
- Censo 2022 e Transferegov existem apenas no pipeline legado do frontend.
- MapBiomas existe apenas no produto de dados.
- Datas, quantidade de municípios e versões ainda estão parcialmente fixas no
  frontend.
- RAWs e Parquets somam centenas de megabytes e não devem ser adicionados ao
  histórico do Git.
- O prazo do concurso exige preservar o MVP funcional durante a consolidação.

## Decisão Arquitetural

O repositório `antes-da-chuva` será o destino definitivo e a única fonte oficial
de código.

```text
antes-da-chuva/
|-- app/                         frontend React atual
|-- src/                         pipelines Python canônicos
|   |-- contracts/
|   |-- extract/
|   |-- transform/
|   `-- validation/
|-- tests/                       testes dos pipelines
|-- scripts/
|   |-- export_frontend_data.py
|   `-- scripts legados temporários
|-- data/
|   |-- raw/                     local, ignorado pelo Git
|   |-- silver/                  local, ignorado pelo Git
|   |-- gold/                    local, ignorado pelo Git
|   |-- manifests/               local ou publicação compacta
|   `-- samples/                 fixtures pequenas versionadas
|-- docs/
|   |-- documentação de produto
|   |-- documentação técnica
|   `-- roadmap/
|-- requirements.txt
`-- README.md
```

O Git versionará código, testes, documentação, amostras pequenas e os JSONs
necessários ao site. RAWs, Parquets e artefatos temporários permanecerão locais.

## Regras Fixas

1. `antes-da-chuva` será a única fonte de código oficial.
2. `codigo_ibge` continuará como string e chave territorial canônica.
3. O pipeline Atlas legado não será mantido como segunda fonte de verdade.
4. Ausência de registro nunca será apresentada como ausência do fenômeno.
5. Nenhum score, previsão, ranking de risco ou causalidade será criado.
6. O frontend não carregará Parquets diretamente.
7. Versões e datas exibidas pela aplicação virão dos manifests.
8. A pasta antiga só será removida após validação e autorização explícita.
9. Cada parte deve terminar com código, testes e documentação coerentes.
10. Nenhuma parte pode deixar o site publicado propositalmente quebrado.

## Tamanhos Das Partes

| Tamanho | Duração esperada | Uso |
|---|---:|---|
| `XS` | Até 2 horas | Ajuste isolado, documentação ou configuração |
| `S` | Até meio dia | Entrega pequena com teste próprio |
| `M` | Até 1 dia | Integração completa que não pode ser dividida com segurança |

Nenhuma parte planejada deve ultrapassar um dia. Caso isso aconteça durante a
execução, ela deve ser dividida antes de continuar.

## Fase 0 - Proteger O MVP

Objetivo: registrar uma referência confiável antes da primeira mudança.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 0.1 | XS | Registrar baseline do site e do JSON atual | Contagens, hashes e casos demonstrativos documentados |
| 0.2 | XS | Executar lint e build atuais | `npm run lint` e `npm run build` aprovados |
| 0.3 | XS | Registrar baseline dos pipelines | 15 testes e três relatórios `PASS` |
| 0.4 | XS | Criar branch de consolidação | `main` permanece funcional e recuperável |
| 0.5 | XS | Definir política de arquivos grandes | Nenhum RAW ou Parquet aparece entre arquivos rastreados pelo Git |

### Gate Da Fase 0

- O frontend atual constrói sem erro.
- O conjunto municipal atual possui hash e métricas registrados.
- Os artefatos do produto de dados coincidem com seus manifests.
- Existe um ponto Git conhecido para retorno.

## Fase 1 - Migrar O Produto De Dados

Objetivo: executar os pipelines dentro do repositório Git sem alterar ainda o
contrato consumido pelo frontend.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 1.1 | XS | Preparar `data/raw`, `data/silver`, `data/gold` e `data/manifests` | Diretórios e regras de `.gitignore` corretos |
| 1.2 | S | Copiar `src/`, `tests/` e `requirements.txt` | Imports preservados, sem refatoração ampla |
| 1.3 | S | Copiar os dados localmente | Hashes iguais aos manifests de origem |
| 1.4 | S | Migrar documentação técnica | Links internos válidos e sem substituir a documentação de produto |
| 1.5 | XS | Migrar prompts para `docs/roadmap/` | Prompts de fontes e interface preservados |
| 1.6 | M | Executar pipelines no repositório Git | IBGE, MapBiomas e Atlas terminam com `PASS` |
| 1.7 | XS | Executar testes no novo local | `python -m pytest -q` com 15 testes aprovados |
| 1.8 | S | Adicionar verificação Python ao CI | CI valida Python e frontend separadamente |

### Mapa De Migração

| Origem | Destino |
|---|---|
| `antesdachuva/src/` | `antes-da-chuva/src/` |
| `antesdachuva/tests/` | `antes-da-chuva/tests/` |
| `antesdachuva/requirements.txt` | `antes-da-chuva/requirements.txt` |
| `antesdachuva/data/raw/` | `antes-da-chuva/data/raw/`, local e ignorado |
| `antesdachuva/data/silver/` | `antes-da-chuva/data/silver/`, local e ignorado |
| `antesdachuva/data/gold/` | `antes-da-chuva/data/gold/`, local e ignorado |
| `antesdachuva/data/manifests/` | `antes-da-chuva/data/manifests/` |
| `antesdachuva/docs/*.md` | `antes-da-chuva/docs/` |
| `antesdachuva/antes-da-chuva-prompts-sources/` | `antes-da-chuva/docs/roadmap/sources/` |
| `antesdachuva/antes-da-chuva-ui-prompts/` | `antes-da-chuva/docs/roadmap/presentation/` |
| `antesdachuva/README.md` | `antes-da-chuva/docs/DATA_PRODUCT.md` |

### Gate Da Fase 1

- Os pipelines funcionam a partir da raiz de `antes-da-chuva`.
- Os testes Python passam no destino.
- O build do frontend continua passando.
- Nenhum arquivo binário grande foi adicionado ao Git.
- A pasta de origem continua intacta.

## Fase 2 - Criar A Ponte Para O Frontend

Objetivo: produzir dados de apresentação a partir das GOLDs sem processar
Parquets no navegador.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 2.1 | S | Documentar o universo territorial | 5.571 unidades vigentes e referência própria do Censo 2022 explícitas |
| 2.2 | M | Comparar Atlas canônico e legado | Diferenças dos códigos comuns explicadas em relatório |
| 2.3 | S | Definir contrato de apresentação v1 | Tipos Python e TypeScript concordantes |
| 2.4 | M | Criar exportador DuckDB para JSON | Frontend não executa joins nem lê Parquets |
| 2.5 | S | Gerar índice municipal compacto | Busca contém as 5.571 unidades vigentes |
| 2.6 | S | Gerar payloads municipais ou shards por UF | Arquivos pequenos e carregamento progressivo |
| 2.7 | S | Gerar metadata das fontes | Release Atlas, coleção MapBiomas e datas vêm dos manifests |
| 2.8 | XS | Validar determinismo | Duas exportações iguais produzem o mesmo hash |
| 2.9 | S | Testar casos de borda | Todos os municípios de referência têm o estado esperado |

### Contrato Inicial De Apresentação

```json
{
  "municipality": {},
  "summary": {},
  "disasters": {
    "history": [],
    "types": [],
    "months": [],
    "highlights": []
  },
  "land_cover": {
    "history": [],
    "change": {}
  },
  "census": {},
  "transfers": {},
  "benchmarks": {},
  "sources": {}
}
```

Censo e Transferegov poderão permanecer temporariamente no formato legado
durante o concurso, mas a transição deverá estar explícita no código e na
documentação. Atlas, IBGE e MapBiomas devem vir exclusivamente das GOLDs.

### Casos Obrigatórios

| Município | Motivo |
|---|---|
| Blumenau/SC | Caso demonstrativo principal |
| São Paulo/SP | Grande volume e capital |
| Rio de Janeiro/RJ | Capital e histórico Atlas |
| Brasília/DF | Tipo territorial especial |
| Fernando de Noronha/PE | Ausência MapBiomas atual |
| Boa Esperança do Norte/MT | Município vigente ausente no universo Censo 2022 |
| Acrelândia/AC | Caso legado sem histórico nem transferência no recorte |
| Bom Jesus da Serra/BA | Transferência sem histórico no recorte legado |
| Milagres do Maranhão/MA | Indicador censitário indisponível |

### Gate Da Fase 2

- Não existe divergência Atlas sem explicação registrada.
- O exportador é determinístico.
- O índice possui códigos únicos e mantém códigos como texto.
- Ausência, zero e falta de cobertura continuam semanticamente distintos.
- A metadata é derivada dos manifests, não de constantes do frontend.

## Fase 3 - Trocar A Fonte Do Frontend

Objetivo: substituir a origem legada sem redesenhar toda a interface de uma só
vez.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 3.1 | S | Consumir o novo índice municipal | Busca por nome, UF e código continua funcionando |
| 3.2 | M | Consumir o payload canônico | Atlas vem exclusivamente das GOLDs |
| 3.3 | XS | Remover fallback silencioso de Blumenau | Falha de dados mostra estado de erro explícito |
| 3.4 | S | Tornar contagens e datas dinâmicas | Nenhuma versão ou quantidade fica fixada no componente |
| 3.5 | S | Tratar ausência por fonte | `null`, zero e ausência de cobertura permanecem distintos |
| 3.6 | XS | Corrigir status Transferegov | Cancelado e anulado recebem tratamento coerente |
| 3.7 | XS | Adicionar link para alertas ativos | IDAP e orientações oficiais ficam separados |
| 3.8 | S | Adicionar testes frontend | Busca, URL, ausência e erro cobertos |
| 3.9 | S | Validar regressão visual | Desktop e mobile preservados |

### Gate Da Fase 3

- O site não usa mais o parser Atlas legado como fonte de verdade.
- A busca cobre 5.571 unidades.
- Links compartilháveis por `codigo_ibge` continuam funcionando.
- O frontend possui estados de loading, erro e ausência.
- `npm run lint`, testes frontend e `npm run build` passam.

## Fase 4 - Incorporar MapBiomas

Esta fase entra antes do concurso somente se as fases anteriores estiverem
estáveis.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 4.1 | S | Exportar resumo territorial | Primeiro ano, último ano e variações disponíveis |
| 4.2 | S | Criar resumo de 30 segundos | Texto determinístico e sem causalidade |
| 4.3 | M | Exibir mudança territorial | Área urbanizada e vegetação nativa com unidade clara |
| 4.4 | XS | Tratar município sem MapBiomas | Ausência não aparece como zero |
| 4.5 | XS | Exibir cautela metodológica | Área urbanizada não é chamada de impermeabilização |
| 4.6 | S | Testar cálculos | Valores reconciliam com as GOLDs |

### Gate Da Fase 4

- Nenhum cálculo MapBiomas é feito no navegador.
- Primeiro e último ano são descobertos nos dados.
- Percentuais e áreas usam unidades explícitas.
- Fernando de Noronha recebe estado de ausência correto.
- A nova seção funciona em desktop e mobile.

## Fase 5 - Fechar A Entrega Do Concurso

Objetivo: produzir uma entrega verificável, reproduzível e pronta para avaliação.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 5.1 | XS | Definir licença | Arquivo `LICENSE` e README alinhados |
| 5.2 | S | Atualizar documentação pública | Estado real, fontes e arquitetura consolidados |
| 5.3 | S | Atualizar checklist do concurso | Evidências associadas a cada critério |
| 5.4 | S | Criar pasta de entregáveis | Capturas, roteiro, descrição e links disponíveis |
| 5.5 | S | Revisar acessibilidade | Teclado, foco, contraste, ARIA e redução de movimento |
| 5.6 | XS | Revisar metadata e imagem social | Dimensões e tamanho do OG corrigidos |
| 5.7 | M | Fazer ensaio em clone limpo | Python, exportação, lint e build reproduzíveis |
| 5.8 | S | Fazer smoke test em produção | Busca, município, fontes e alertas funcionando |
| 5.9 | XS | Criar release do concurso | Tag, commit e artefatos identificáveis |

### Gate Da Fase 5

- O site de produção funciona sem erros bloqueadores.
- Código, metodologia e fontes estão publicamente documentados.
- A entrega pode ser reproduzida a partir de um clone limpo.
- As evidências do concurso estão organizadas.
- A release submetida possui tag e hash Git conhecidos.

## Fase 6 - Robustecer Os Pipelines

Executar depois da entrega do concurso. Cada correção deve ser independente e
ter um teste de regressão próprio.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 6.1 | S | Criar fingerprint semântico da dimensão | `ingested_at` não força reconstrução do Atlas |
| 6.2 | S | Incluir dimensão na assinatura MapBiomas | Mudança territorial invalida o produto corretamente |
| 6.3 | S | Validar hashes antes de `NO_CHANGE` | Arquivo corrompido não é aceito |
| 6.4 | M | Publicar bundles transacionais | Falha parcial preserva a versão anterior |
| 6.5 | S | Arquivar por mudança de assinatura | Mesmo ID com hash novo gera histórico |
| 6.6 | M | Tornar referência monetária dinâmica | Nova release Atlas não exige índice fixo de 2025 |
| 6.7 | M | Uniformizar manifests | IBGE, MapBiomas e Atlas usam os mesmos estados |
| 6.8 | XS | Remover caminhos absolutos | Manifests ficam portáveis entre máquinas |
| 6.9 | M | Criar fixtures offline | Testes não dependem de rede ou Parquets existentes |
| 6.10 | S | Adicionar lint e formatação Python | Verificação automática no CI |

## Fase 7 - Evoluir A Experiência

Seguir os prompts de apresentação já existentes, uma entrega por vez.

| Ordem | Bloco | Verificação mínima |
|---:|---|---|
| 1 | Resumo de 30 segundos | Texto determinístico e estados ausentes |
| 2 | Histórico anual relacionado à chuva | Série municipal e média regional reconciliadas |
| 3 | Tipos COBRADE | Percentuais e ordenação testados |
| 4 | Perfil mensal | Doze meses e total reconciliado |
| 5 | Mudança do território | Série e janelas temporais reconciliadas |
| 6 | Comparação regional | Universo, média, mediana e missing documentados |
| 7 | Anos de destaque | Seleção e desempate determinísticos |
| 8 | Fontes e limitações | Metadata refletindo os manifests atuais |

Cada bloco deverá incluir transformação, payload, componente, tratamento de
ausência, acessibilidade e testes antes de iniciar o próximo.

## Fase 8 - Canonizar As Fontes Restantes

A ordem recomendada muda em relação ao roadmap original porque Censo e
Transferegov já fazem parte do produto publicado.

| Ordem | Fonte ou produto | Entrega principal |
|---:|---|---|
| 1 | Censo 2022/SIDRA 6805 | Pipeline RAW/SILVER/GOLD e indicador direto preservando ausências |
| 2 | Transferegov | Entidades relacionais, classificação auditável e snapshots municipais |
| 3 | ICM | Capacidade institucional oficial por ciclo |
| 4 | SINISA | Infraestrutura e serviços de saneamento |
| 5 | MIDR | Municípios prioritários e cadastro nacional |
| 6 | Cemaden | Inventário e cobertura municipal |
| 7 | SGB | Suscetibilidade geológica oficial |
| 8 | População em áreas de risco | Exposição oficial disponível |
| 9 | `municipality_source_coverage` | Disponibilidade por município e fonte |
| 10 | `source_freshness` | Atualidade e estado operacional das fontes |
| 11 | `python -m src.all_sources` | Orquestração com status independente por fonte |

Censo entra antes de ICM porque já é parte central da promessa publicada e ainda
não possui pipeline canônico. Somente uma nova fonte deve estar em implementação
por vez.

## Fase 9 - Encerrar A Transição

Objetivo: eliminar duplicações somente depois que a nova arquitetura estiver
comprovada.

| Parte | Tam. | Entrega | Critério de aceite |
|---|---:|---|---|
| 9.1 | S | Remover parser Atlas legado | Paridade aprovada e frontend usando GOLD |
| 9.2 | S | Remover gerador JSON legado | Exportador canônico cobre todas as fontes usadas |
| 9.3 | M | Executar duas atualizações completas | Segunda execução retorna `NO_CHANGE` quando aplicável |
| 9.4 | S | Auditar arquivos exclusivos da pasta antiga | Nenhum código, documento ou dado necessário permanece apenas na origem |
| 9.5 | XS | Arquivar `antesdachuva` | Cópia segura e referência do último estado registradas |
| 9.6 | XS | Excluir a pasta antiga | Somente após autorização explícita |

## Cronograma Sugerido Para O Concurso

| Data | Foco |
|---|---|
| 02/09 | Baseline e preparação do Git |
| 03/09 | Migração dos pipelines |
| 04/09 | Exportador e paridade Atlas |
| 05/09 | Troca da fonte do frontend |
| 06/09 | MapBiomas, se o núcleo estiver estável |
| 07/09 | Testes, acessibilidade e validação |
| 08/09 | Documentação, evidências e release |
| 09/09 | Submissão e apenas correções bloqueadoras |

## Linha De Corte

Para o concurso, são obrigatórias:

- Fase 0: baseline;
- Fase 1: migração;
- Fase 2: ponte de dados;
- Fase 3: troca da fonte do frontend;
- Fase 5: fechamento da entrega.

A Fase 4 só entra antes da submissão se não ameaçar a estabilidade do MVP. As
Fases 6, 7, 8 e 9 são evolução posterior e não devem bloquear a entrega.

## Comandos De Verificação

### Produto De Dados

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python -m pytest -q
```

### Frontend

```bash
cd app
npm ci
npm run lint
npm run build
```

### Git

```bash
git status --short
git ls-files data
```

O resultado esperado da verificação Git é não encontrar RAWs, Parquets,
ambientes virtuais, dependências Node ou artefatos de build entre os arquivos
rastreados.

## Definição De Pronto

Uma parte só pode ser considerada concluída quando:

1. a entrega funciona no repositório de destino;
2. os testes relacionados passam;
3. a documentação afetada foi atualizada;
4. dados ausentes mantêm sua semântica correta;
5. versões e períodos permanecem auditáveis;
6. o build atual do frontend continua funcionando;
7. nenhum arquivo grande ou segredo foi adicionado ao Git;
8. o resultado pode ser revisado independentemente da próxima parte.

## Riscos E Respostas

| Risco | Resposta planejada |
|---|---|
| Adicionar centenas de MB ao Git | Configurar e verificar `.gitignore` antes da cópia |
| Manter duas fontes de verdade | Trocar Atlas por paridade e desativar o legado depois |
| Divergência de 5.570 e 5.571 unidades | Modelar referência temporal e não excluir Boa Esperança do Norte |
| Quebrar o site durante a migração | Preservar contrato atual até o exportador estar validado |
| Perder prazo com escopo visual | Aplicar a linha de corte e tornar MapBiomas opcional antes do concurso |
| Interpretar ausência como zero | Testes explícitos de ausência por fonte |
| Exibir metadata desatualizada | Gerar versões e datas a partir dos manifests |
| Classificar transferência incorretamente | Preservar evidência, status e regra de atribuição |
| Remover a origem cedo demais | Arquivar e excluir somente após autorização |
| Licença indefinida | Resolver antes da release submetida ao concurso |

## Resultado Esperado

Ao final da consolidação, o repositório `antes-da-chuva` deverá conter a
experiência web, os pipelines canônicos, o exportador de apresentação, os testes
e toda a documentação necessária. O site consumirá somente derivados produzidos
pelas GOLDs e por pipelines oficiais das fontes restantes, sem duplicação Atlas,
sem versões fixadas manualmente e sem depender da pasta `antesdachuva`.
