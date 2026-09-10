async function request(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) { const error = new Error(payload?.error?.message || `Request failed (${response.status})`); error.status = response.status; error.code = payload?.error?.code; error.current = payload?.error?.current; throw error; }
  return payload;
}
export const api = {
  listDocuments(status = 'all') { return request(`/api/documents?status=${encodeURIComponent(status)}`); },
  getDocument(id) { return request(`/api/documents/${encodeURIComponent(id)}`); },
  addManualRedaction(id, payload) { return request(`/api/documents/${encodeURIComponent(id)}/redactions`, { method: 'POST', body: JSON.stringify(payload) }); },
};
