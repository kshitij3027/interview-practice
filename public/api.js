async function request(url, options = {}) {
  let response;
  try { response = await fetch(url, options); }
  catch { throw new Error('Network unavailable; reload to retry'); }
  const body = await response.json();
  if (!response.ok) { const error = new Error(body?.error?.message || `HTTP ${response.status}`); error.code = body?.error?.code; error.status = response.status; throw error; }
  return body;
}
const query = params => new URLSearchParams(params).toString();
export const api = {
  organizations: () => request('/api/organizations'),
  customers: org => request('/api/customers?' + query({org})),
  flags: (org, search, status) => request('/api/flags?' + query({org,search,status})),
  detail: (org, id) => request('/api/flags/' + encodeURIComponent(id) + '?' + query({org})),
  note: (org, id, note, expectedRevision) => request('/api/flags/' + encodeURIComponent(id) + '/note?' + query({org}), {method:'PATCH', headers:{'content-type':'application/json'}, body:JSON.stringify({note,expectedRevision})})
};
