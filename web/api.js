async function request(path, options) {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return body;
}

export function listCustomers(segment = "") {
  const query = segment ? `?segment=${encodeURIComponent(segment)}` : "";
  return request(`/api/customers${query}`);
}

export function getCustomer(id) {
  return request(`/api/customers/${encodeURIComponent(id)}`);
}

export function setCustomerStatus(id, status, expectedRevision) {
  return request(`/api/customers/${encodeURIComponent(id)}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, expected_revision: expectedRevision })
  });
}
