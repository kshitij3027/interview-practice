async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status})`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

export const api = {
  listCampaigns(status = "all") {
    const query = status === "all" ? "" : `?status=${encodeURIComponent(status)}`;
    return request(`/api/campaigns${query}`);
  },
  getCampaign(id) {
    return request(`/api/campaigns/${encodeURIComponent(id)}`);
  },
  setStatus(id, status, expectedRevision) {
    return request(`/api/campaigns/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, expected_revision: expectedRevision }),
    });
  },
};
