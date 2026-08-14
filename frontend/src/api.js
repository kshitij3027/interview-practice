const API = 'http://localhost:3001/api';

async function json(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail?.message ?? `Request failed (${response.status})`;
    throw new Error(message);
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
};
