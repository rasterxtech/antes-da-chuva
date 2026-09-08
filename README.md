<div align="center">
  <img src="app/public/favicon-v2.svg" width="96" alt="Símbolo do Antes da Chuva">

  # Antes da Chuva · v1

  **Antes da próxima chuva, conheça sua cidade.**

  [![Site](https://img.shields.io/badge/site-antesdachuva.info-176b64?style=for-the-badge)](https://antesdachuva.info)
  [![CI](https://img.shields.io/github/actions/workflow/status/rasterxtech/antes-da-chuva/ci.yml?branch=main&style=for-the-badge&label=build)](https://github.com/rasterxtech/antes-da-chuva/actions/workflows/ci.yml)
  [![Dados abertos](https://img.shields.io/badge/dados-fontes%20públicas-245e91?style=for-the-badge)](docs/FONTES_DE_DADOS.md)
  [![Licença](https://img.shields.io/badge/licença-Apache%202.0-17364a?style=for-the-badge)](LICENSE)
</div>

![Interface editorial do Antes da Chuva](docs/design/2026-09-08/desktop.png)

*Interface do Antes da Chuva v1. Consulte o deployment indicado no PR para conferir a versão correspondente.*

O **Antes da Chuva** transforma bases públicas dispersas em uma leitura municipal curta, rastreável e acessível. Ao buscar uma cidade, a pessoa encontra o histórico de ocorrências ligadas à chuva, uma condição estrutural que pode ampliar danos, estruturas e instrumentos de prevenção declarados pela prefeitura, evidências de prevenção financiada pela União, mudanças observadas na cobertura da terra e caminhos oficiais para receber alertas.

O projeto foi criado para o **2º Concurso de Reúso de Dados Abertos da CGU, edição 2026**. Este repositório documenta o estado do código e dos dados de apresentação; a confirmação de uma implantação, submissão, homologação ou release é controlada separadamente no [checklist de entrega](docs/CRITERIOS_DO_CONCURSO.md).

## Produto

A experiência combina um resumo de 30 segundos com capítulos para aprofundar a leitura:

1. O que as chuvas já causaram neste município?
2. Qual condição estrutural pode ampliar o impacto?
3. Que estruturas e instrumentos de prevenção a prefeitura declarou possuir em 2020?
4. Que ações federais de prevenção aparecem nas bases consultadas?
5. Como o território mudou e como o município se compara à sua região?
6. Onde receber alertas oficiais da Defesa Civil?

O produto não prevê desastres, não atribui nota de proteção e não trata a ausência de registros como prova de ausência de política pública.

## Funcionalidades

- Busca por nome, UF exata ou código entre 5.571 unidades territoriais analíticas vigentes do IBGE, sem seleção automática de termos ambíguos.
- Resumo municipal e navegação pelos capítulos Histórico, Território e Preparação.
- Histórico de cinco tipologias relacionadas à chuva entre 1991 e 2025, com filtro, série anual, perfil mensal e comparação regional.
- Indicador de saneamento do Censo Demográfico 2022, ainda em transição para pipeline canônico.
- Nove estruturas e instrumentos de gestão de riscos declarados pelas prefeituras na MUNIC 2020.
- Evidências selecionadas de transferências e parcerias da União, ainda em transição para pipeline canônico.
- Cobertura e uso da terra pelo MapBiomas, com alternância percentual/km², períodos de comparação e ausência de cobertura explícita.
- Comparação com a Região Geográfica Imediata, com unidades, universo e limitações; não é um ranking de risco.
- Acesso direto aos canais oficiais de alerta da Defesa Civil.
- Fontes e limitações apresentadas junto de cada informação.
- Interface responsiva com menu móvel, foco visível, navegação por teclado e alternativas tabulares para os gráficos principais. A avaliação completa de acessibilidade continua em andamento.

## Ambientes e entrega

| Ambiente | Branch | Endereço |
| --- | --- | --- |
| Produção | `main` | [antesdachuva.info](https://antesdachuva.info/) |
| Homologação | `staging` | [stg.antesdachuva.info](https://stg.antesdachuva.info/) |
| Candidato de cada PR | Branch de trabalho | Preview informado pela Vercel no PR |

A Vercel publica os ambientes a partir da integração Git. O domínio `www.antesdachuva.info` redireciona para o principal. STG e previews mantêm a proteção de acesso configurada na Vercel; pertencer ao GitHub não concede automaticamente acesso à equipe Vercel.

Cada versão passa por revisão, testes e homologação antes da publicação. Consulte o [registro de homologação](docs/HOMOLOGACAO_DESIGN_STAGING.md) e o [fluxo de release](docs/FLUXO_DE_RELEASE.md). Nenhuma mudança isolada deve ser promovida diretamente para `main`.

## Fontes públicas

| Fonte | Uso no produto | Estado no contrato de apresentação |
| --- | --- | --- |
| [IBGE - API de Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id) | Dimensão territorial municipal vigente | Canônica: gera identidade e índice municipal |
| [Atlas Digital de Desastres no Brasil](https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml) | Registros municipais de alagamentos, enxurradas, inundações, movimentos de massa e chuvas intensas | Canônica: derivada das GOLDs; registros administrativos podem conter lacunas |
| [MapBiomas Brasil](https://brasil.mapbiomas.org/downloads/estatisticas/) | Cobertura e uso da terra por município | Canônica: derivada das GOLDs; ausência de cobertura não é zero |
| [MUNIC 2020 - IBGE](https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-deinformacoes-basicas-municipais.html?edicao=32141) | Estruturas e instrumentos de gestão de riscos declarados pelas prefeituras | Canônica: integra o contrato de apresentação v1 como evidência declaratória referente a 2020 |
| [Censo Demográfico 2022, tabela 6805](https://sidra.ibge.gov.br/tabela/6805) | Percentual de domicílios fora das formas selecionadas de esgotamento sanitário | Transicional: reempacotado do payload legado; não mede risco hidrológico |
| [Transferências e Parcerias da União](https://dados.gov.br/dados/conjuntos-dados/transferencias-e-parcerias-da-uniao) | Programas e propostas federais selecionados por ação, objeto e atribuição municipal | Transicional: proposta não equivale a política municipal completa |
| [Defesa Civil](https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/alertas-de-desastres-1) | Orientação para receber alertas oficiais | Serviço externo: o site não emite nem replica alertas em tempo real |

A avaliação completa de qualidade, escopo e limites está em [Auditoria das fontes](docs/AUDITORIA_FONTES.md).

## Tecnologias

- React 19 e TypeScript
- Tailwind CSS
- Recharts para séries e comparações; Bricolage Grotesque e Atkinson Hyperlegible para identidade e leitura
- Next.js 16 com App Router
- Vercel como plataforma de deploy, com homologação separada de produção
- Python e DuckDB para a consolidação reproduzível das bases

## Executar localmente

Pré-requisitos:

- Node.js 22.x (22.13 ou superior nessa linha)
- npm 11.6.2

```bash
git clone https://github.com/rasterxtech/antes-da-chuva.git
cd antes-da-chuva/app
npm ci
npm run dev
```

A aplicação ficará disponível no endereço informado pelo terminal, normalmente `http://localhost:3000`.

No Windows, você pode usar PowerShell na pasta do clone; WSL não é obrigatório para desenvolver o frontend. Na primeira execução, o projeto baixa e valida o pacote público de apresentação fixado em `app/presentation-data-release.json`. Não é necessário obter as bases brutas para trabalhar na interface.

Para validar o frontend, a partir da raiz do repositório:

```bash
node --test .github/scripts/check-pr-target.test.cjs
cd app
npm ci
npm run lint
npm test
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

Para exploração e testes rápidos, consulte as [amostras reduzidas para colaboradores](data/samples/README.md). Elas cobrem as 27 unidades federativas e casos de presença e ausência de dados. O JSON de amostra tem formato legado; não substitui o contrato v1 usado pelo frontend atual.

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

Saída local, deliberadamente excluída do histórico Git:

```text
app/public/data/v1/metadata.json
app/public/data/v1/municipal-index.json
app/public/data/v1/uf/<UF>.json ou <UF>-<parte>.json
```

Os payloads v1 são reproduzíveis e não acompanham o repositório. O arquivo
`app/presentation-data-release.json` fixa a URL e o SHA 256 do artefato público
usado nos builds. `npm run dev`, `npm run build` e `npm run start` materializam
automaticamente esse pacote quando os arquivos locais não existem. Quem estiver trabalhando na camada de dados pode
regenerar a saída com `python scripts/export_frontend_data.py`; nesse caso, o
build valida e preserva a cópia local.

O artefato publicado contém apenas JSONs derivados que já são servidos pelo
site. Bases brutas, SILVERs e GOLDs continuam fora do Git e são compartilhadas
separadamente com a equipe.

Os shards preservam o alvo de 24 MiB adotado originalmente para compatibilidade
com a hospedagem anterior. Isso não significa que a aplicação ainda esteja no
Sites/Cloudflare. Uma UF que excede o alvo é publicada em partes determinísticas;
o índice aponta cada município para sua parte.

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
- [Homologação e produção](docs/FLUXO_DE_RELEASE.md)
- [Revisão crítica de design](docs/REVISAO_DESIGN_2026-09-08.md)
- [Plano de melhorias visuais](docs/PLANO_DESIGN_STAGING.md)
- [Candidato visual, testes e roteiro de aceite](docs/HOMOLOGACAO_DESIGN_STAGING.md)
- [Licença, autoria e reutilização](docs/LICENCIAMENTO.md)

## Contribuição

O desenvolvimento segue o fluxo `feature → staging → main`. A `staging` é o destino padrão dos PRs e reúne as funcionalidades para homologação. A `main` recebe somente PRs vindos da `staging` após a validação da equipe.

As duas branches exigem verificações automáticas e aprovação de outra pessoa, incluindo o último envio. Consulte o [guia de contribuição](CONTRIBUTING.md) e o [fluxo de homologação e produção](docs/FLUXO_DE_RELEASE.md). A integração de uma funcionalidade usa squash em `staging`; a promoção homologada usa merge commit de `staging` para `main`.

Falhas de segurança não devem ser publicadas em issues. Siga as instruções da [política de segurança](SECURITY.md).

## Licença

Código e documentação originais sob [Apache License 2.0](LICENSE). Redistribuições devem preservar os avisos aplicáveis de autoria e atribuição, incluindo o [NOTICE](NOTICE), conforme a licença.

Titulares, em ordem alfabética: **Felipe Flumignan, Felipe Liske, Isabella Grimaldi, Isabelle Camargo e Leoni Leopoldino**.

A licença permite uso comercial e não exige abertura de todas as modificações nem crédito obrigatório no rodapé de sites derivados. Dados, dependências e marcas têm condições próprias. Consulte o [guia de licenciamento](docs/LICENCIAMENTO.md).

## Qualidade e transparência

As verificações, capturas e limitações dos testes ficam no
[registro de homologação](docs/HOMOLOGACAO_DESIGN_STAGING.md). Os ensaios de
reprodução identificam seus commits em [Reprodução](docs/REPRODUCAO.md).
A participação no concurso segue o [checklist de entrega](docs/CRITERIOS_DO_CONCURSO.md),
sem confundir código disponível com inscrição ou homologação concluída.
