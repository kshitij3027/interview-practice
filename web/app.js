import {addNote, loadCase, loadCases} from './api.js';
import {state, setCases, setSelected} from './store.js';

const list = document.querySelector('#case-list');
const detail = document.querySelector('#detail');
const errorEl = document.querySelector('#error');
const statusFilter = document.querySelector('#status-filter');
const priorityFilter = document.querySelector('#priority-filter');

function esc(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }

function renderList() {
  list.innerHTML = state.cases.map(c => `<button class="case-row" data-id="${esc(c.id)}"><b>${esc(c.customer)}</b><span>${esc(c.status)} · ${esc(c.priority)}</span><small>${esc(c.owner_email || 'unassigned')} · r${c.revision}</small></button>`).join('') || '<p>No cases match.</p>';
  list.querySelectorAll('[data-id]').forEach(button => button.addEventListener('click', () => selectCase(button.dataset.id)));
}

function renderDetail() {
  const c = state.selectedCase;
  if (!c) { detail.innerHTML = '<p>Select a case.</p>'; return; }
  detail.innerHTML = `<h2>${esc(c.customer)}</h2><p>${esc(c.external_ref)} · external v${c.external_version} · revision ${c.revision}</p><p>Status: <b>${esc(c.status)}</b> · Priority: <b>${esc(c.priority)}</b> · Owner: ${esc(c.owner_email || 'unassigned')}</p><h3>Internal notes</h3><ul>${c.notes.map(n => `<li>${esc(n.text)}</li>`).join('') || '<li>None</li>'}</ul><form id="note-form"><input id="note-text" placeholder="Internal note"><button>Add note</button></form>`;
  document.querySelector('#note-form').addEventListener('submit', submitNote);
}

async function refreshCases() {
  errorEl.textContent = '';
  try {
    const data = await loadCases(state.filters);
    setCases(data.cases);
    renderList();
  } catch (err) { errorEl.textContent = err.message; }
}

async function selectCase(id) {
  try { const data = await loadCase(id); setSelected(data.case); renderDetail(); }
  catch (err) { errorEl.textContent = err.message; }
}

async function submitNote(event) {
  event.preventDefault();
  const text = document.querySelector('#note-text').value;
  try {
    const data = await addNote(state.selectedCase.id, text, state.selectedCase.revision);
    setSelected(data.case);
    renderDetail();
    await refreshCases();
  } catch (err) {
    errorEl.textContent = err.message;
    if (err.status === 409) await selectCase(state.selectedCase.id);
  }
}

statusFilter.addEventListener('change', () => { state.filters.status = statusFilter.value; refreshCases(); });
priorityFilter.addEventListener('change', () => { state.filters.priority = priorityFilter.value; refreshCases(); });
refreshCases();
