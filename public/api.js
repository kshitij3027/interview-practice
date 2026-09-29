async function request(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || 'request failed (' + response.status + ')');
    error.status = response.status;
    error.body = body;
    throw error;
  }
  return body;
}

export function fetchSuites(filters) {
  const params = new URLSearchParams();
  if (filters.owner) params.set('owner', filters.owner);
  if (filters.status) params.set('status', filters.status);
  return request('/api/suites?' + params);
}

export function fetchSuite(id) {
  return request('/api/suites/' + encodeURIComponent(id));
}

export function saveNote(id, note, expectedRevision) {
  return request('/api/suites/' + encodeURIComponent(id) + '/note', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ note, expectedRevision })
  });
}
