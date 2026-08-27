const BASE = '/api';
async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {headers:{'Content-Type':'application/json'}, ...options});
  const body = await response.json();
  if (!response.ok) { const error = new Error(body.error || 'request_failed'); error.status = response.status; throw error; }
  return body;
}
export const api = {
  listAccounts: segment => request(`/accounts${segment ? `?segment=${encodeURIComponent(segment)}` : ''}`),
  accountDetail: id => request(`/accounts/${encodeURIComponent(id)}`),
  setOverride: (id, payload) => request(`/accounts/${encodeURIComponent(id)}/override`, {method:'POST', body:JSON.stringify(payload)})
};
