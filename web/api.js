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
  funnel: (segment = 'all', delayMs = 0) => {
    const params = new URLSearchParams({ segment });
    // Omitted entirely when zero, so ordinary requests carry no debug parameter.
    if (delayMs > 0) params.set('delay_ms', String(delayMs));
    return request(`/api/funnel?${params}`);
  },
  setExclusion: (userId, excluded, reason = '') => request(`/api/users/${encodeURIComponent(userId)}/exclusion`, {
    method: 'PATCH',
    body: JSON.stringify({ excluded, reason })
  })
};
