const API = 'http://localhost:3001/api';

async function json(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail?.message ?? `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.code = body?.detail?.code;
    throw error;
  }
  return response.json();
}

export const api = {
  accounts: () => fetch(`${API}/accounts`).then(json),
  account: (id) => fetch(`${API}/accounts/${id}`).then(json),
  addCredit: (id, amountCents, reason) => fetch(`${API}/accounts/${id}/credits`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ amountCents, reason }),
  }).then(json),
  previewSettlement: (csvText) => fetch(`${API}/settlements/preview`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ csv_text: csvText }),
  }).then(json),
  commitSettlement: (previewId) => fetch(`${API}/settlements/commit`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ preview_id: previewId }),
  }).then(json),
};
