# Como contribuir

Obrigado pelo interesse no Antes da Chuva. O projeto combina produto digital, dados públicos e comunicação de risco. Toda mudança deve preservar rastreabilidade, clareza e responsabilidade na apresentação das evidências.

## Formas de participação

- Abra uma issue para relatar um problema ou propor uma melhoria.
- Envie um pull request com uma alteração pequena e verificável.
- Se você faz parte da equipe oficial, trabalhe em uma branch própria e nunca diretamente na `main`.

Ser colaborador convidado concede permissões adicionais no repositório, mas não permite ignorar as proteções da branch principal.

## Preparar o ambiente

```bash
git clone git@github.com:rasterxtech/antes-da-chuva.git
cd antes-da-chuva/app
npm ci
npm run dev
```

Requisitos: Node.js 22.13 ou superior e npm 10 ou superior.

## Fluxo de trabalho

1. Crie ou escolha uma issue para contextualizar a mudança.
2. Atualize sua branch local a partir da `main`.
3. Crie uma branch com um nome objetivo, como `feat/busca-por-estado`, `fix/fonte-card` ou `docs/metodologia`.
4. Faça commits pequenos, em português ou inglês, com mensagens claras.
5. Execute as verificações locais.
6. Abra um pull request usando o modelo do repositório.
7. Aguarde o build e pelo menos uma aprovação.

## Verificações obrigatórias

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
- relacionar a issue correspondente quando existir;
- manter o build aprovado.

O merge é feito por squash. A branch é removida depois da integração.

## Segurança

Não publique vulnerabilidades, tokens ou credenciais em issues. Use o canal privado descrito em [SECURITY.md](SECURITY.md).
