async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status})`);
    error.status = response.status;
    error.details = body.details;
    throw error;
  }
  return body;
}

export const api = {
  employees: () => request('/api/employees'),
  shifts: (site = 'all') => request(`/api/shifts?site=${encodeURIComponent(site)}`),
  shift: (id) => request(`/api/shifts/${encodeURIComponent(id)}`),
  reassign: (id, employeeId, expectedRevision) => request(`/api/shifts/${encodeURIComponent(id)}/assignee`, {
    method: 'PATCH',
    body: JSON.stringify({ employee_id: employeeId, expected_revision: expectedRevision }),
  }),
};
