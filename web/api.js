const API = 'http://localhost:3001/api';

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {headers: {'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || 'request_failed');
    error.status = response.status;
    throw error;
  }
  return data;
}

export function loadCases(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.priority) params.set('priority', filters.priority);
  const suffix = params.toString() ? `?${params}` : '';
  return request(`/cases${suffix}`);
}

export function loadCase(id) { return request(`/cases/${encodeURIComponent(id)}`); }
export function addNote(id, text, expectedRevision) {
  return request(`/cases/${encodeURIComponent(id)}/notes`, {method:'POST', body:JSON.stringify({text, expected_revision:expectedRevision})});
}
