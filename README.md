<div align="center">
  <img src="app/public/brand-mark.png" width="112" alt="Símbolo do Antes da Chuva">

  # Antes da Chuva

  **Inteligência pública municipal para compreender riscos e fortalecer a prevenção.**

  [![Site](https://img.shields.io/badge/site-antesdachuva.info-176b64?style=for-the-badge)](https://antesdachuva.info)
  [![CI](https://img.shields.io/github/actions/workflow/status/rasterxtech/antes-da-chuva/ci.yml?branch=main&style=for-the-badge&label=build)](https://github.com/rasterxtech/antes-da-chuva/actions/workflows/ci.yml)
  [![Dados abertos](https://img.shields.io/badge/dados-fontes%20oficiais-245e91?style=for-the-badge)](docs/FONTES_DE_DADOS.md)
</div>

![Prévia do Antes da Chuva](app/public/og.png)

O **Antes da Chuva** transforma bases públicas dispersas em uma leitura municipal curta, rastreável e acessível. Ao buscar uma cidade, a pessoa encontra o histórico de ocorrências ligadas à chuva, uma condição estrutural que pode ampliar danos, estruturas e instrumentos de prevenção declarados pela prefeitura, evidências de prevenção financiada pela União, mudanças observadas na cobertura da terra e caminhos oficiais para receber alertas.

O projeto foi criado para o **2º Concurso de Reúso de Dados Abertos da CGU, edição 2026**. Este repositório documenta o estado do código e dos dados de apresentação; a confirmação de uma implantação, submissão, homologação ou release é controlada separadamente no [checklist de entrega](docs/CRITERIOS_DO_CONCURSO.md).

## Produto

A experiência foi desenhada para responder, em menos de um minuto:

1. O que as chuvas já causaram neste município?
2. Qual condição estrutural pode ampliar o impacto?
3. Que estruturas e instrumentos de prevenção a prefeitura declarou possuir em 2020?
4. Que ações federais de prevenção aparecem nas bases consultadas?
5. Onde receber alertas oficiais da Defesa Civil?

O produto não prevê desastres, não atribui nota de proteção e não trata a ausência de registros como prova de ausência de política pública.

## Funcionalidades

- Busca entre 5.571 unidades territoriais analíticas vigentes do IBGE, usando o código IBGE como chave.
- Histórico municipal de cinco tipologias relacionadas à chuva entre 1991 e 2025.
- Indicador de saneamento do Censo Demográfico 2022, ainda em transição para pipeline canônico.
- Nove estruturas e instrumentos de gestão de riscos declarados pelas prefeituras na MUNIC 2020.
- Evidências selecionadas de transferências e parcerias da União, ainda em transição para pipeline canônico.
- Cobertura e uso da terra pelo MapBiomas, com período e ausência de cobertura explícitos.
- Acesso direto aos canais oficiais de alerta da Defesa Civil.
- Fontes e limitações apresentadas junto de cada informação.
- Interface responsiva, acessível e otimizada para leitura rápida.

## Fontes públicas

| Fonte | Uso no produto | Estado no contrato de apresentação |
| --- | --- | --- |
| [IBGE - API de Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id) | Dimensão territorial municipal vigente | Canônica: gera identidade e índice municipal |
| [Atlas Digital de Desastres no Brasil](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) | Registros municipais de alagamentos, enxurradas, inundações, movimentos de massa e chuvas intensas | Canônica: derivada das GOLDs; registros administrativos podem conter lacunas |
| [MapBiomas Brasil](https://brasil.mapbiomas.org/) | Cobertura e uso da terra por município | Canônica: derivada das GOLDs; ausência de cobertura não é zero |
| [MUNIC 2020 - IBGE](https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-deinformacoes-basicas-municipais.html?edicao=32141) | Estruturas e instrumentos de gestão de riscos declarados pelas prefeituras | Canônica: integra o contrato de apresentação v1 como evidência declaratória referente a 2020 |
| [Censo Demográfico 2022, tabela 6805](https://sidra.ibge.gov.br/tabela/6805) | Percentual de domicílios fora das formas selecionadas de esgotamento sanitário | Transicional: reempacotado do payload legado; não mede risco hidrológico |
| [Transferências e Parcerias da União](https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao) | Programas e propostas federais selecionados por ação, objeto e atribuição municipal | Transicional: proposta não equivale a política municipal completa |
| [Defesa Civil](https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/alertas-de-desastres-1) | Orientação para receber alertas oficiais | Serviço externo: o site não emite nem replica alertas em tempo real |

A avaliação completa de qualidade, escopo e limites está em [Auditoria das fontes](docs/AUDITORIA_FONTES.md).

## Tecnologias

- React 19 e TypeScript
- Tailwind CSS
- Vite e Vinext
- Cloudflare Workers no artefato de produção
- Python e DuckDB para a consolidação local das bases

## Executar localmente

Pré-requisitos:

- Node.js 22.13 ou superior
- npm 11.6.2

```bash
git clone git@github.com:rasterxtech/antes-da-chuva.git
cd antes-da-chuva/app
npm ci
npm run dev
```

A aplicação ficará disponível no endereço informado pelo terminal, normalmente `http://localhost:3000`.

Para validar o mesmo processo executado no CI:

```bash
cd app
npm ci
npm run lint
npm run build
```

## Arquitetura de dados

```text
Fontes oficiais
       |
       v
Pipelines Python -> RAW / SILVER / GOLD locais e ignorados pelo Git
       |              (IBGE, Atlas, MapBiomas e MUNIC)
       v
export_frontend_data.py -> JSON público v1 por UF/partes
       |                    (índice, metadata e shards)
       v
Aplicação React -> busca no índice e carrega somente o shard indicado
```

Os pipelines canônicos de IBGE, MapBiomas, Atlas/S2ID e MUNIC estão em `src/`, com
testes em `tests/`. O navegador consome apenas JSON do contrato de apresentação
v1, sem abrir Parquet nem executar junções. Censo e Transferegov seguem
declarados como transicionais no próprio contrato. Consulte a
[metodologia](docs/METODOLOGIA.md), o [contrato v1](docs/CONTRATO_APRESENTACAO_V1.md),
a [documentação do produto de dados](docs/DATA_PRODUCT.md) e a
[política de dados locais](docs/DADOS_LOCAIS_E_MANIFESTS.md).

A execução completa requer acesso às fontes oficiais e espaço local para os
artefatos ignorados. Este clone não contém esses dados, portanto consultas aos
Parquets e os testes de saídas materializadas permanecem bloqueados até uma
execução local. Os testes unitários e de descoberta podem ser executados sem
esses artefatos:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

O exportador abaixo requer GOLDs locais materializadas. Ele usa o payload legado
somente para Censo e Transferegov transicionais; Atlas, IBGE, MapBiomas e MUNIC vêm das
GOLDs. O navegador consome somente o contrato v1, sem ler o payload legado.

Para exploração e testes rápidos, consulte as [amostras reduzidas para colaboradores](data/samples/README.md). Elas cobrem as 27 unidades federativas e casos de presença e ausência de dados nas três dimensões do produto.

Entradas locais esperadas:

```text
data/raw/atlas_1991_2025.xlsx
data/raw/censo_6805_percentual_rede.json
data/raw/siconv_programa.csv.zip
data/raw/siconv_programa_proposta.csv.zip
data/raw/siconv_proposta.csv.zip
data/raw/siconv_convenio.csv.zip
data/raw/munic/2020/Base_MUNIC_2020.xlsx
```

Geração do contrato publicado (com as GOLDs locais materializadas):

```bash
python scripts/export_frontend_data.py
```

Saída local, deliberadamente excluída do Git:

```text
app/public/data/v1/metadata.json
app/public/data/v1/municipal-index.json
app/public/data/v1/uf/<UF>.json ou <UF>-<parte>.json
```

Os payloads v1 são reproduzíveis e não acompanham o repositório. Antes de
executar a aplicação com dados municipais reais, materialize as GOLDs locais e
execute `python scripts/export_frontend_data.py`.

Os shards usam alvo de 24 MiB para permanecer abaixo do limite de asset de 25 MiB
da Cloudflare. Uma UF que excede o alvo e publicada em partes deterministicas;
o indice aponta cada municipio para sua parte.

## Verificação e reprodução

O teste do exportador materializa Parquets temporários a partir de fixtures
versionadas. Ele verifica o contrato e o determinismo sem exigir o conjunto
completo de dados:

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests/test_presentation_export.py
python -m pytest -q

cd app
npm ci
npm run lint
npm test
npm run build
```

Para ensaiar as verificações em um clone do commit atual, após o commit estar
disponível no Git, execute:

```bash
scripts/verify_clean_clone.sh
```

O ensaio não baixa fontes oficiais, não materializa as GOLDs completas e não
substitui a validação de uma implantação. A sequência completa, seus pré-requisitos
e seus limites estão em [Reprodução](docs/REPRODUCAO.md).

## Estrutura do repositório

```text
antes-da-chuva/
├── app/                 aplicação web e contrato de apresentação público
├── src/                 pipelines canônicos de dados
├── tests/               testes dos pipelines canônicos
├── data/raw/            fontes originais locais, ignoradas pelo Git
├── data/silver/         derivados normalizados locais, ignorados pelo Git
├── data/gold/           produtos analíticos locais, ignorados pelo Git
├── data/manifests/      manifests JSON compactos versionados
├── data/processed/      intermediários do pipeline legado, locais
├── docs/                metodologia, decisões e critérios do concurso
├── scripts/             exportador e scripts de apoio
└── .github/             CI, segurança e modelos de colaboração
```

## Documentação

- [Plano mestre](docs/PLANO_MESTRE.md)
- [Critérios do concurso](docs/CRITERIOS_DO_CONCURSO.md)
- [Registro de decisões](docs/DECISOES.md)
- [Inventário de fontes](docs/FONTES_DE_DADOS.md)
- [Auditoria das fontes](docs/AUDITORIA_FONTES.md)
- [Metodologia](docs/METODOLOGIA.md)
- [Reprodução](docs/REPRODUCAO.md)
- [Acessibilidade](docs/ACESSIBILIDADE.md)
- [Produto de dados](docs/DATA_PRODUCT.md)
- [Dados locais e manifests](docs/DADOS_LOCAIS_E_MANIFESTS.md)
- [Baseline da consolidação](docs/BASELINE_CONSOLIDACAO.md)

## Contribuição

Alterações na branch `main` são feitas exclusivamente por pull request, com build obrigatório e aprovação de outra pessoa. Consulte o [guia de contribuição](CONTRIBUTING.md) antes de começar.

Falhas de segurança não devem ser publicadas em issues. Siga as instruções da [política de segurança](SECURITY.md).

## Licença

A licença do código e seu titular ainda serão definidos pelos responsáveis antes
da submissão oficial. Não há arquivo `LICENSE` enquanto essa decisão não for
formalizada. Os dados permanecem sujeitos aos termos e às condições de suas
fontes de origem.

## Estado do projeto

O checkout contém os resultados de código das fases 0 a 4: pipelines canônicos,
contrato de apresentação v1, testes e a interface que consome o contrato. A
execução completa dos pipelines, o ensaio em clone limpo, a validação em produção,
a licença, a submissão e uma release identificada requerem confirmações externas
ou artefatos locais e estão marcados como pendentes nos documentos de entrega.
