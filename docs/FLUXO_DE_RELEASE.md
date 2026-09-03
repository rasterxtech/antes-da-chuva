# Homologação e produção

O fluxo do time é `feature → staging → main`. A validação funcional ocorre antes da promoção para produção, sem publicar cada funcionalidade isoladamente.

| Branch | Papel | Destino dos PRs | Ambiente a vincular na Vercel |
| --- | --- | --- | --- |
| `feat/*`, `fix/*`, `docs/*` e outras branches de trabalho | Mudança isolada | `staging` | Preview por PR, se habilitado |
| `staging` | Integração e homologação, branch padrão do GitHub | `main`, após homologação | Staging ou Preview da branch `staging` |
| `main` | Código aprovado para produção | Sem desenvolvimento direto | Production |

## Proteções do GitHub

As duas branches permanentes exigem:

- alterações por PR, sem bypass de administrador;
- pelo menos uma aprovação de outra pessoa e aprovação do último envio;
- nova revisão quando novos commits invalidarem a aprovação;
- resolução das conversas da revisão;
- verificações `Build` e `Branch policy` aprovadas com a base atualizada;
- bloqueio de exclusão e de force push.

A política automática rejeita PRs para `main` que não venham da `staging` do próprio repositório. Uma branch com o mesmo nome em um fork não pode ser usada para promover código. Essa validação depende do workflow de CI; alterações em `.github/` devem ser revisadas com especial atenção.

As configurações das proteções são administradas no GitHub, não por este documento. Na implantação inicial deste fluxo, o PR de configuração precisa ser aprovado e integrado à `staging` antes dos PRs de funcionalidades: ele adiciona o CI necessário à nova branch.

## 1. Desenvolver e integrar uma funcionalidade

```bash
git fetch origin
git switch -c feat/minha-feature origin/staging
```

Desenvolva e teste a alteração. Depois de enviar a branch, abra o PR com base `staging`. Com aprovação e verificações concluídas, use **Squash and merge**. A branch temporária pode ser removida.

## 2. Homologar e promover

1. Aguarde o deployment do estado atual da `staging` no ambiente de homologação da Vercel.
2. Teste busca de municípios, fontes, dados, alertas oficiais e as funcionalidades alteradas, incluindo telas grandes e móveis.
3. Registre no PR de promoção o link do deployment testado, o commit validado e o responsável pela homologação.
4. Abra o PR com **base `main`** e **compare `staging`**. Nenhuma funcionalidade deve ser adicionada à `staging` entre a homologação final e o merge; se houver novos commits, repita a validação.
5. Aguarde outra pessoa aprovar e as verificações passarem.
6. Use **Create a merge commit**. Não use squash nem rebase na promoção, e não remova a `staging`.
7. Quando a integração com a Vercel estiver configurada, acompanhe o deployment de Production e confira a versão no domínio público.

O merge commit preserva a relação entre as duas branches permanentes e evita reapresentar o histórico inteiro em promoções futuras. A configuração da `main` permite somente esse método. Na `staging`, merge commit também é permitido para sincronizações; funcionalidades normalmente usam squash. [Referência do GitHub](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges).

## 3. Sincronizar o histórico após a promoção

O merge de promoção cria um novo commit na `main`. Traga esse histórico de volta à `staging` por uma branch temporária, sem criar commits diretamente em nenhuma das branches protegidas:

```bash
git fetch origin
git switch -c sync/main-into-staging origin/staging
git merge origin/main
git push -u origin sync/main-into-staging
```

Abra um PR dessa branch temporária para `staging`, aguarde aprovação e verificações e use **Create a merge commit**, não squash. Resolva qualquer conflito na branch temporária. Se o nome já existir, use outro nome `sync/*` disponível. O procedimento funciona mesmo se novas funcionalidades já tiverem entrado na `staging`; não é necessário modificar a `main` para sincronizar.

## Configuração da Vercel

O repositório usa Next.js 16 com App Router e o preset nativo da Vercel. O arquivo `app/vercel.json` fixa `npm ci` para instalação e `npm run build` para compilação. A configuração de produção anterior do Sites/Cloudflare foi removida do código; o histórico do Git preserva a versão anterior para referência.

Configurações do repositório não criam automaticamente projetos, ambientes ou domínios. Antes de vincular o domínio público, valide o deployment da migração na Vercel; mantenha a hospedagem antiga disponível até concluir essa conferência e o corte de DNS.

Após essa validação, no projeto correto da Vercel:

1. Configure **Root Directory** como `app`, **Framework Preset** como **Next.js** e **Node.js Version** como **22.x**. Use `npm ci`, `npm run build` e o diretório de saída padrão do Next.js (`.next`), sem apontar para o antigo `dist`.
2. Em **Settings → Environments → Production → Branch Tracking**, selecione explicitamente `main`, mesmo que a branch padrão do GitHub seja `staging`.
3. Vincule `staging` a um ambiente customizado de homologação, se disponível no plano. Como alternativa, use o Preview dessa branch com domínio e variáveis específicos.
4. Se desejar `staging.antesdachuva.info`, configure esse domínio para a branch ou ambiente de homologação, separado do domínio de Production. Nenhuma alteração de DNS é realizada por este documento.
5. Separe variáveis e credenciais de homologação e produção. Não exponha segredos em variáveis do frontend, e não versione arquivos `.env`.
6. Verifique que um merge em `staging` atualiza somente homologação, e que um merge em `main` dispara Production. Confirme também a associação automática do domínio de produção se a publicação deve ocorrer sem etapa manual.
7. Faça um teste completo do fluxo antes de liberar a publicação no domínio público.

O CI do GitHub valida o código; ele não contém credenciais nem passos de deploy. A publicação automática depende da integração Git e da configuração de ambientes da Vercel. [Branches e deploys na Vercel](https://vercel.com/docs/git). [Alternativas para staging por plano](https://vercel.com/kb/guide/set-up-a-staging-environment-on-vercel).

## Se uma versão apresentar problemas

Pause novas promoções. Um mantenedor deve avaliar o rollback para um deployment conhecido no painel da Vercel, quando a hospedagem estiver migrada. Depois, a correção ou reversão deve passar por uma branch de trabalho, PR para `staging`, homologação e PR de promoção para `main`. Não faça force push, não exclua as branches permanentes e não desative as proteções para contornar uma falha.
