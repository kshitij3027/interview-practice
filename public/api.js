export async function request(path, options = {}) {
  let response;
  try { response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } }); }
  catch { throw new Error('Network failure — check the connection and retry.'); }
  let payload;
  try { payload = await response.json(); } catch { throw new Error('Server returned an unreadable response.'); }
  if (!response.ok) { const error = new Error(payload.error?.message ?? `HTTP ${response.status}`); error.status = response.status; error.code = payload.error?.code; throw error; }
  return payload;
}
export const getCatalog = () => request('/api/catalog');
export const listJobs = (account, search, status) => request(`/api/jobs?${new URLSearchParams({ account, search, status, limit: '100' })}`);
export const getJob = (account, id) => request(`/api/jobs/${encodeURIComponent(id)}?${new URLSearchParams({ account })}`);
export const saveNote = (account, id, body) => request(`/api/jobs/${encodeURIComponent(id)}/note?${new URLSearchParams({ account })}`, { method: 'PATCH', body: JSON.stringify(body) });
