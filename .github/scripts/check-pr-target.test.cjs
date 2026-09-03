const { test } = require('node:test');
const assert = require('node:assert/strict');
const { validatePullRequest } = require('./check-pr-target.cjs');

function event(base, head, headRepo = 'rasterxtech/antes-da-chuva') {
  return { pull_request: {
    base: { ref: base, repo: { full_name: 'rasterxtech/antes-da-chuva' } },
    head: { ref: head, repo: { full_name: headRepo } },
  } };
}

test('funcionalidade do time entra em staging', () => {
  assert.doesNotThrow(() => validatePullRequest(event('staging', 'feat/busca')));
});

test('contribuição por fork entra em staging', () => {
  assert.doesNotThrow(() => validatePullRequest(event('staging', 'feat/busca', 'contribuidor/fork')));
});

test('staging do próprio repositório pode ser promovida para main', () => {
  assert.doesNotThrow(() => validatePullRequest(event('main', 'staging')));
});

test('funcionalidade não pode ir diretamente para main', () => {
  assert.throws(() => validatePullRequest(event('main', 'feat/busca')), /devem vir da staging/);
});

test('branch chamada staging em um fork não pode ir para main', () => {
  assert.throws(() => validatePullRequest(event('main', 'staging', 'contribuidor/fork')), /devem vir da staging/);
});

test('sincronização pode entrar em staging', () => {
  assert.doesNotThrow(() => validatePullRequest(event('staging', 'sync/main-into-staging')));
});

test('outros destinos são rejeitados', () => {
  assert.throws(() => validatePullRequest(event('outra-branch', 'feat/busca')), /destino deve ser/);
});

test('evento incompleto é rejeitado', () => {
  assert.throws(() => validatePullRequest({}), /identificar/);
  const incomplete = event('main', 'staging');
  incomplete.pull_request.head.repo = null;
  assert.throws(() => validatePullRequest(incomplete), /identificar/);
});
