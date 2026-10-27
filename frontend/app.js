import { api } from './api.js';

const $ = (id) => document.getElementById(id);
const state = { tenant: null, selected: null, detail: null, listSeq: 0, detailSeq: 0, noteBusy: false };
const options = (q) => new URLSearchParams(q).toString();
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const report = (message) => { $('status-line').textContent = message; };
const fmt = (date) => new Date(date).toLocaleString([], {dateStyle:'medium', timeStyle:'short', timeZone:'UTC'}) + ' UTC';

async function loadList() {
  const seq = ++state.listSeq;
  const tenant = state.tenant;
  const status = $('status').value;
  const q = $('search').value;
  try {
    const data = await api('/api/visits?' + options({tenant, status, q}));
    if (seq !== state.listSeq || tenant !== state.tenant) return;
    $('count').textContent = `${data.total} matches`;
    $('visits').innerHTML = data.items.map((v) => `
      <button type="button" class="visit ${v.id === state.selected ? 'active' : ''}" data-id="${escapeHtml(v.id)}">
        <strong>${escapeHtml(v.vendorName)} <span class="badge">${escapeHtml(v.status)}</span></strong>
        <small>${escapeHtml(v.id)} · ${escapeHtml(v.siteName)}</small>
        <small>${fmt(v.startAt)} · ${escapeHtml(v.purpose)}</small>
      </button>`).join('') || '<p>No visits match these filters.</p>';
    $('visits').querySelectorAll('[data-id]').forEach((button) => button.addEventListener('click', () => select(button.dataset.id)));
  } catch (error) { if (seq === state.listSeq) report(error.message); }
}

async function select(id) {
  state.selected = id;
  state.detail = null;
  $('notes').hidden = true;
  $('summary').innerHTML = '<p>Loading visit details…</p>';
  const seq = ++state.detailSeq;
  const tenant = state.tenant;
  loadList();
  try {
    const data = await api('/api/visits/' + encodeURIComponent(id) + '?' + options({tenant}));
    if (seq !== state.detailSeq || state.selected !== id || state.tenant !== tenant) return;
    state.detail = data.visit;
    const v = data.visit;
    $('summary').innerHTML = `
      <span class="badge">${escapeHtml(v.status)}</span>
      <h2>${escapeHtml(v.purpose)}</h2><p>${escapeHtml(v.id)} · ${escapeHtml(v.vendorName)}</p>
      <dl class="meta"><div><dt>Site</dt><dd>${escapeHtml(v.siteName)}</dd></div>
      <div><dt>Vendor status</dt><dd>${v.vendorActive ? 'Active' : 'Inactive'}</dd></div>
      <div><dt>Arrival (UTC)</dt><dd>${fmt(v.startAt)}</dd></div>
      <div><dt>Departure (UTC)</dt><dd>${fmt(v.endAt)}</dd></div>
      <div><dt>Visit revision</dt><dd>${v.revision}</dd></div>
      <div><dt>Pass reference</dt><dd>${escapeHtml(v.issuedPassId || 'Not issued')}</dd></div></dl>`;
    $('note').value = v.note;
    $('note-status').textContent = '';
    $('notes').hidden = false;
  } catch (error) { if (seq === state.detailSeq) { $('summary').textContent = error.message; report(error.message); } }
}

async function saveNote() {
  if (!state.detail || state.noteBusy) return;
  const id = state.selected;
  const tenant = state.tenant;
  const old = state.detail;
  const note = $('note').value;
  state.noteBusy = true;
  $('save-note').disabled = true;
  $('note-status').textContent = 'Saving…';
  try {
    const data = await api('/api/visits/' + encodeURIComponent(id) + '/note?' + options({tenant}), {
      method: 'PATCH', body: JSON.stringify({note, expectedRevision: old.revision}),
    });
    if (state.selected === id && state.tenant === tenant) {
      state.detail = data.visit;
      $('note-status').textContent = 'Saved';
      if (data.visit.note === note.trim()) $('note').value = data.visit.note;
      await select(id);
    }
    await loadList();
  } catch (error) {
    if (state.selected === id && state.tenant === tenant) {
      $('note-status').textContent = error.status === 409 ? 'Changed elsewhere. Refresh the visit before trying again.' : error.message;
      if (error.status === 409) report('Stale edit. Your unsaved note remains in the editor.');
    }
  } finally { state.noteBusy = false; $('save-note').disabled = false; }
}

$('tenant').addEventListener('change', () => {
  state.tenant = $('tenant').value;
  state.selected = null;
  state.detail = null;
  ++state.detailSeq;
  $('summary').innerHTML = '<p>Select a visit to see its details.</p>';
  $('notes').hidden = true;
  loadList();
});
$('status').addEventListener('change', loadList);
$('search').addEventListener('input', () => loadList());
$('save-note').addEventListener('click', saveNote);

async function boot() {
  try {
    const data = await api('/api/tenants');
    $('tenant').innerHTML = data.tenants.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    state.tenant = data.tenants[0];
    await loadList();
    report('Workspace loaded.');
  } catch (error) { report(error.message); }
}
boot();
