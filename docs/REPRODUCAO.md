# Reprodução e verificação

## Escopo verificável no checkout

Este repositório permite testar o código Python, o exportador contra fixtures e
a aplicação frontend sem baixar as bases completas. Isso não equivale a uma
reprodução integral das fontes oficiais, de suas GOLDs ou de uma implantação.

| Nível | O que é executável | O que não demonstra |
|---|---|---|
| Testes Python | Contratos, transformações unitárias e exportação v1 com fixtures temporárias | Materialização nacional das fontes oficiais |
| Testes frontend | Busca, URL, estados de ausência e falhas de carregamento com respostas simuladas | Resposta de uma implantação real |
| Build frontend | Compilação do artefato local | Publicação, cache, domínio ou smoke test em produção |
| Clone limpo | Instalação e verificações acima a partir de um commit | Pipeline completo de dados ou implantação |

## Pré-requisitos locais

- Python 3.13, alinhado ao CI atual.
- Node.js 22.13 ou superior e npm 11.6.2.
- Acesso à rede para instalar dependências. A execução completa dos pipelines
  também requer acesso às fontes oficiais e espaço para dados locais.

## Verificações com fixtures

Na raiz do repositório:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests/test_presentation_export.py
python -m pytest -q
```

`tests/test_presentation_export.py` cria Parquets temporários a partir de
`tests/fixtures/presentation_v1/`, executa o exportador e verifica contrato,
determinismo e casos de borda. Ele não escreve as GOLDs completas no repositório.
Os testes que inspecionam saídas materializadas podem ser ignorados quando as
GOLDs locais não existem; o motivo aparece no próprio pytest.

No frontend:

```bash
cd app
npm ci
npm run lint
npm test
npm run build
```

## Ensaio em clone limpo

Após disponibilizar o commit a testar no Git, execute na raiz:

```bash
scripts/verify_clean_clone.sh
```

O script clona o `HEAD` em diretório temporário, exige que esteja limpo, instala
as dependências e executa os testes Python com fixtures, todos os testes Python,
lint, testes e build do frontend. Ele falha deliberadamente se o próprio script
ainda não estiver presente no `HEAD`; mudanças não commitadas não fazem parte do
ensaio.

Registre a saída, o hash do commit, o sistema operacional e as versões de Python,
Node e npm somente depois de uma execução concluída. Não marque o ensaio como
concluído antecipadamente.

### Ensaio registrado

Em 3 de setembro de 2026, o script foi executado com sucesso no commit
`39581e28fc1748b2f014bdae7a9b10c56b7547ee`, em Linux, com Python 3.13.5,
Node.js v24.14.1 e npm 11.11.0. No clone temporário, os testes de exportação
com fixtures terminaram em `5 passed`; a suíte Python terminou em `18 passed,
2 skipped` (as duas verificações dependem intencionalmente das GOLDs locais);
lint, testes frontend (`10 passed`) e build também terminaram com sucesso.

## Reprodução completa das fontes

Esta sequência é um procedimento para quando as fontes e os recursos locais
estiverem disponíveis; não foi executada por este documento:

```bash
python -m src.pipeline
python -m src.mapbiomas
python -m src.atlas
python scripts/export_frontend_data.py
python -m pytest -q
```

Antes de executá-la, confirme URLs oficiais, disponibilidade das fontes, espaço
em disco, hashes e limites metodológicos. RAW, SILVER e GOLD permanecem locais e
ignorados pelo Git. Consulte [DADOS_LOCAIS_E_MANIFESTS.md](DADOS_LOCAIS_E_MANIFESTS.md)
e [DATA_PRODUCT.md](DATA_PRODUCT.md) para os artefatos e as dependências entre
etapas.
