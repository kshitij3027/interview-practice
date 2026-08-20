const BASE = 'http://127.0.0.1:3001';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error || 'Request failed');
    error.status = response.status;
    throw error;
  }
  return payload;
}

export const api = {
  accounts: () => request('/api/accounts'),
  plans: () => request('/api/plans'),
  account: (id) => request(`/api/accounts/${encodeURIComponent(id)}`),
  changeCurrentPlan: (id, planKey, expectedRevision) => request(`/api/accounts/${encodeURIComponent(id)}/current-plan`, {
    method: 'POST',
    body: JSON.stringify({ plan_key: planKey, expected_revision: expectedRevision }),
  }),
};
