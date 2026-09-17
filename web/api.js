async function request(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const err = new Error(body.error || `Request failed (${response.status})`); err.status = response.status; err.body = body; throw err; }
  return body;
}
export const api = {
  config: () => request('/api/config'),
  listReturns: ({ warehouse = '', status = '' } = {}) => request(`/api/returns?warehouse=${encodeURIComponent(warehouse)}&status=${encodeURIComponent(status)}`),
  getReturn: id => request(`/api/returns/${encodeURIComponent(id)}`),
  setException: (id, payload) => request(`/api/returns/${encodeURIComponent(id)}/exception`, { method: 'PUT', body: JSON.stringify(payload) })
};
