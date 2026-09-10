import { api } from './api.js';
import { state, setError } from './store.js';
const root = document.querySelector('#app');
function escapeHtml(value) { return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'); }
function render() {
  const detail = state.detail?.document;
  root.innerHTML = `<header><div><h1>RedactDesk</h1><p>Document review console</p></div><div class="revision">Dataset r${state.datasetRevision ?? '—'}</div></header>${state.error ? `<div class="error">${escapeHtml(state.error)}</div>` : ''}<main><aside><label>Status<select id="status-filter">${['all','reviewing','approved'].map((v) => `<option value="${v}" ${state.statusFilter === v ? 'selected' : ''}>${v}</option>`).join('')}</select></label><div class="document-list">${state.loadingList ? '<p>Loading…</p>' : state.documents.map((doc) => `<button class="document-row ${doc.id === state.selectedId ? 'selected' : ''}" data-doc-id="${doc.id}"><strong>${escapeHtml(doc.title)}</strong><span>${doc.status} · r${doc.revision} · ${doc.redactionCount} redaction(s)</span></button>`).join('') || '<p>No documents.</p>'}</div></aside><section>${state.loadingDetail ? '<p>Loading document…</p>' : detail ? renderDetail(detail) : '<p>Select a document.</p>'}</section></main>`;
  bind();
}
function renderDetail(doc) {
  return `<div class="detail-heading"><div><h2>${escapeHtml(doc.title)}</h2><p>${doc.id} · ${doc.status} · revision ${doc.revision}</p></div></div><div class="pages">${doc.pages.map((page) => `<article class="page"><h3>Page ${page.number}</h3><pre>${escapeHtml(page.text)}</pre><div class="offsets">Offsets: 0 … ${page.text.length}</div></article>`).join('')}</div><h3>Current redactions</h3><table><thead><tr><th>ID</th><th>Page</th><th>Range</th><th>Category</th><th>Source</th><th>Note</th></tr></thead><tbody>${doc.redactions.map((r) => `<tr><td>${r.id}</td><td>${r.page}</td><td>[${r.start}, ${r.end})</td><td>${r.category}</td><td>${r.source}</td><td>${escapeHtml(r.note)}</td></tr>`).join('') || '<tr><td colspan="6">None</td></tr>'}</tbody></table><form id="redaction-form" class="card ${doc.status !== 'reviewing' ? 'disabled' : ''}"><h3>Add manual redaction</h3><div class="form-grid"><label>Page<input name="page" type="number" min="1" value="1" required></label><label>Start<input name="start" type="number" min="0" required></label><label>End<input name="end" type="number" min="1" required></label><label>Category<select name="category"><option>personal</option><option>financial</option><option>credentials</option></select></label></div><label>Note<input name="note" maxlength="120" required></label><button ${doc.status !== 'reviewing' || state.savingRedaction ? 'disabled' : ''}>${state.savingRedaction ? 'Saving…' : 'Add redaction'}</button></form>`;
}
function bind() {
  document.querySelector('#status-filter')?.addEventListener('change', async (event) => { state.statusFilter = event.target.value; await loadDocuments(true); });
  document.querySelectorAll('[data-doc-id]').forEach((button) => button.addEventListener('click', async () => { state.selectedId = button.dataset.docId; await loadDetail(state.selectedId); }));
  document.querySelector('#redaction-form')?.addEventListener('submit', addRedaction);
}
async function loadDocuments(keepSelection = false) {
  state.loadingList = true; setError(); render();
  try { const result = await api.listDocuments(state.statusFilter); state.documents = result.documents; state.datasetRevision = result.datasetRevision; if (!keepSelection || !state.documents.some((doc) => doc.id === state.selectedId)) state.selectedId = state.documents[0]?.id ?? null; }
  catch (error) { setError(error.message); }
  finally { state.loadingList = false; render(); }
  if (state.selectedId) await loadDetail(state.selectedId);
}
async function loadDetail(id) {
  state.loadingDetail = true; setError(); render();
  try { const result = await api.getDocument(id); if (state.selectedId !== id) return; state.detail = result; state.datasetRevision = Math.max(state.datasetRevision ?? 0, result.datasetRevision); }
  catch (error) { setError(error.message); }
  finally { state.loadingDetail = false; render(); }
}
async function addRedaction(event) {
  event.preventDefault(); if (!state.detail?.document || state.savingRedaction) return; const form = new FormData(event.currentTarget); const id = state.detail.document.id;
  const payload = { page: Number(form.get('page')), start: Number(form.get('start')), end: Number(form.get('end')), category: String(form.get('category')), note: String(form.get('note')), expectedRevision: state.detail.document.revision };
  state.savingRedaction = true; setError(); render();
  try { const result = await api.addManualRedaction(id, payload); if (state.selectedId === id) state.detail = result; state.datasetRevision = result.datasetRevision; const summary = state.documents.find((doc) => doc.id === id); if (summary) { summary.revision = result.document.revision; summary.redactionCount = result.document.redactions.length; } }
  catch (error) { setError(error.message); if (error.code === 'stale_revision' && state.selectedId === id) await loadDetail(id); }
  finally { state.savingRedaction = false; render(); }
}
loadDocuments();
