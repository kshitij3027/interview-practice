const BASE = 'http://localhost:3001/api';

async function json(path, opts) {
  const r = await fetch(BASE + path, opts);
  const b = await r.json();
  if (!r.ok) {
    const e = new Error(b.error || 'request_failed');
    e.status = r.status;
    e.body = b;
    throw e;
  }
  return b;
}

const postJson = body => ({
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify(body)
});

export const api = {
  loadAccounts: () => json('/flags/smart-compose/accounts'),
  setOverride: (accountId, enabled, expectedRevision) => json(
    '/flags/smart-compose/override',
    postJson({ accountId, enabled, expectedRevision })
  ),
  loadCohorts: () => json('/flags/smart-compose/cohorts'),
  previewRollout: (cohortId, percentage, excludeIds) => json(
    '/flags/smart-compose/rollout/preview',
    postJson({ cohortId, percentage, excludeIds })
  ),
  applyRollout: (inputSnapshot, expectedRevision, requestId) => json(
    '/flags/smart-compose/rollout/apply',
    postJson({ ...inputSnapshot, expectedRevision, requestId })
  )
};
