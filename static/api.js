async function request(url, options={}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status})`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}
export function listFlags(filters={}) {
  const p = new URLSearchParams();
  if (filters.status) p.set("status", filters.status);
  if (filters.owner) p.set("owner", filters.owner);
  return request(`/api/flags${p.toString() ? "?" + p : ""}`);
}
export function getFlag(id) { return request(`/api/flags/${encodeURIComponent(id)}`); }
export function saveNote(id, expectedRevision, note) {
  return request(`/api/flags/${encodeURIComponent(id)}/note`, {
    method:"PATCH", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({expectedRevision,note})
  });
}
