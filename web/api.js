const API_BASE = 'http://localhost:3001';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'content-type': 'application/json', ...(options.headers ?? {}) }
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? `HTTP ${response.status}`);
  return body;
}

export const api = {
  overview: () => request('/api/overview'),
  users: () => request('/api/users'),
  setExclusion: (userId, excluded, reason = '') => request(`/api/users/${encodeURIComponent(userId)}/exclusion`, {
    method: 'PATCH',
    body: JSON.stringify({ excluded, reason })
  })
};
