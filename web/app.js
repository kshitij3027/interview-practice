const el = id => document.getElementById(id);
const state = { contactId: null, contact: null, listToken: 0, detailToken: 0 };
const html = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || `HTTP ${response.status}`);
  return payload;
}

async function loadCampaigns() {
  try {
    const result = await api('/api/campaigns');
    el('campaigns').innerHTML = result.items.map(c => `<p><strong>${html(c.name)}</strong><br><span class="pill">${html(c.status)}</span> ${html(c.channel)} · ${html(c.segment)}<br><span class="muted">${html(c.message)}</span></p>`).join('');
  } catch (error) { el('campaigns').textContent = error.message; }
}

async function loadContacts() {
  const token = ++state.listToken;
  const params = new URLSearchParams({q:el('search').value, segment:el('segment').value, status:el('status').value});
  try {
    const result = await api(`/api/contacts?${params}`);
    if (token !== state.listToken) return;
    el('count').textContent = `${result.total} matching contacts`;
    el('contacts').replaceChildren();
    for (const contact of result.items) {
      const button = document.createElement('button');
      button.className = 'row';
      button.textContent = `${contact.name} · ${contact.segment} · ${contact.status}`;
      button.addEventListener('click', () => chooseContact(contact.id));
      el('contacts').append(button);
    }
  } catch (error) { if (token === state.listToken) el('count').textContent = error.message; }
}

async function chooseContact(id) {
  const token = ++state.detailToken;
  state.contactId = id;
  state.contact = null;
  el('detail').textContent = 'Loading…';
  el('note-form').hidden = true;
  el('notice').textContent = '';
  try {
    const contact = await api(`/api/contacts/${encodeURIComponent(id)}`);
    if (token !== state.detailToken || id !== state.contactId) return;
    state.contact = contact;
    el('detail').innerHTML = `<h3>${html(contact.name)}</h3><p>${html(contact.phone)} · ${html(contact.status)} · ${html(contact.segment)}</p><p class="muted">ID ${html(contact.id)} · revision ${contact.revision}</p>`;
    el('note').value = contact.note;
    el('note-form').hidden = false;
  } catch (error) { if (token === state.detailToken) el('detail').textContent = error.message; }
}

el('note-form').addEventListener('submit', async event => {
  event.preventDefault();
  const contact = state.contact;
  if (!contact) return;
  const value = el('note').value;
  try {
    const updated = await api(`/api/contacts/${encodeURIComponent(contact.id)}/note`, { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({expectedRevision:contact.revision, note:value}) });
    if (state.contactId !== contact.id || state.contact?.revision !== contact.revision) return;
    state.contact = updated;
    el('notice').textContent = 'Saved.';
    el('detail').querySelector('.muted').textContent = `ID ${updated.id} · revision ${updated.revision}`;
  } catch (error) { if (state.contactId === contact.id) el('notice').textContent = error.message; }
});
for (const id of ['search','segment','status']) el(id).addEventListener(id === 'search' ? 'input' : 'change', loadContacts);
await Promise.all([loadCampaigns(),loadContacts()]);
