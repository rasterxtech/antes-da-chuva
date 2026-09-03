const { readFileSync } = require('node:fs');

function validatePullRequest(event) {
  const { base, head } = event.pull_request ?? {};
  if (!base?.ref || !head?.ref || !base.repo?.full_name || !head.repo?.full_name) {
    throw new Error('Não foi possível identificar a origem e o destino do PR.');
  }

  if (base.ref !== 'main' && base.ref !== 'staging') {
    throw new Error('O destino deve ser staging ou main.');
  }

  if (base.ref === 'main' &&
      (head.ref !== 'staging' || head.repo.full_name !== base.repo.full_name)) {
    throw new Error('PRs para main devem vir da staging deste repositório. Envie funcionalidades para staging.');
  }
}

if (require.main === module) {
  if (process.env.GITHUB_EVENT_NAME === 'workflow_dispatch') {
    console.log('Execução manual: não há destino de PR para validar.');
  } else if (process.env.GITHUB_EVENT_NAME === 'pull_request') {
    validatePullRequest(JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8')));
    console.log('Fluxo do PR válido.');
  } else {
    throw new Error('Evento não suportado pela política de branches.');
  }
}

module.exports = { validatePullRequest };
