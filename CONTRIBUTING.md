# Como contribuir

Obrigado pelo interesse no Antes da Chuva. O projeto combina produto digital, dados públicos e comunicação de risco. Toda mudança deve preservar rastreabilidade, clareza e responsabilidade na apresentação das evidências.

## Formas de participação

- Abra uma issue para relatar um problema ou propor uma melhoria.
- Envie um pull request com uma alteração pequena e verificável.
- Se você faz parte da equipe oficial, trabalhe em uma branch própria e nunca diretamente na `staging` ou na `main`.

Ser colaborador convidado concede permissões adicionais no repositório, mas não permite ignorar as proteções das branches permanentes.

## Preparar o ambiente

```bash
git clone git@github.com:rasterxtech/antes-da-chuva.git
cd antes-da-chuva/app
npm ci
npm run dev
```

Requisitos: Node.js 22.x (22.13 ou superior nessa linha) e npm 11.6.2.

## Fluxo de trabalho

1. Crie ou escolha uma issue para contextualizar a mudança.
2. Atualize sua branch local a partir da `staging`, destino padrão dos novos PRs.
3. Crie uma branch com um nome objetivo, como `feat/busca-por-estado`, `fix/fonte-card` ou `docs/metodologia`.
4. Faça commits pequenos, em português ou inglês, com mensagens claras.
5. Execute as verificações locais.
6. Abra um pull request com destino à `staging`, usando o modelo do repositório.
7. Aguarde as verificações `Build` e `Branch policy`, além de pelo menos uma aprovação de outra pessoa.
8. Integre a funcionalidade usando **Squash and merge**. A equipe homologa o conjunto em `stg.antesdachuva.info`, vinculado ao Preview da branch `staging` na Vercel.

Para começar uma funcionalidade:

```bash
git fetch origin
git switch -c feat/minha-feature origin/staging
```

Se você já iniciou uma funcionalidade a partir da `main`, incorpore `origin/staging` à sua branch, resolva eventuais conflitos e abra o PR com destino à `staging`.

Depois da homologação, um mantenedor abre um PR da `staging` para a `main` e usa **Create a merge commit**, preservando a branch `staging`. Funcionalidades isoladas não entram diretamente na `main`.

Consulte [Homologação e produção](docs/FLUXO_DE_RELEASE.md) para promoção, sincronização entre branches e configuração dos ambientes na Vercel.

## Verificações obrigatórias

Na raiz do repositório, valide também a política de branches:

```bash
node --test .github/scripts/check-pr-target.test.cjs
```

Na pasta `app`:

```bash
npm run lint
npm test
npm run build
```

Toda mudança no exportador ou no contrato deve executar a exportação com
fixtures versionadas:

```bash
python -m pytest -q tests/test_presentation_export.py
```

Quando a mudança afetar uma GOLD, um manifest ou a saída pública v1 e as GOLDs
locais estiverem materializadas, execute também:

```bash
python scripts/export_frontend_data.py
```

Confira `app/public/data/v1/metadata.json`, `municipal-index.json` e os shards
por UF; descreva no pull request quais fontes e recortes foram modificados. Não
trate o teste com fixtures como substituto de uma exportação completa.

## Regras para dados e conteúdo

- Cite a fonte oficial ao lado da informação que ela sustenta.
- Registre limitações, recortes temporais e ausência de dados de forma explícita.
- Não transforme ausência de registro em valor zero ou em conclusão positiva.
- Não apresente o produto como previsão meteorológica, alerta oficial ou laudo técnico.
- Não versione bases brutas, arquivos temporários, credenciais ou dados pessoais.
- Atualize a documentação metodológica quando uma regra de negócio mudar.

## Pull requests

Um pull request deve:

- resolver um objetivo principal;
- explicar o problema e a solução;
- indicar como a mudança foi testada;
- incluir imagens quando houver alteração visual;
- usar o [roteiro de homologação visual](docs/HOMOLOGACAO_DESIGN_STAGING.md) como referência e registrar cenários realmente testados;
- relacionar a issue correspondente quando existir;
- manter o build aprovado.

PRs de funcionalidades para `staging` usam squash, e suas branches temporárias podem ser removidas depois da integração. PRs de promoção (`staging` para `main`) e de sincronização de histórico usam merge commit. Nunca remova `staging` ou `main`.

## Licença das contribuições

O código original usa [Apache License 2.0](LICENSE). Ao enviar uma contribuição intencionalmente para inclusão, observe a seção 5 da licença e confirme que possui os direitos ou a autorização necessária. Preserve LICENSE, NOTICE e os avisos de terceiros. Consulte o [guia de licenciamento](docs/LICENCIAMENTO.md) para créditos, dados públicos e marca.

## Segurança

Não publique vulnerabilidades, tokens ou credenciais em issues. Use o canal privado descrito em [SECURITY.md](SECURITY.md).
