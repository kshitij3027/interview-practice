import { fetchSuite, fetchSuites, saveNote } from './api.js';
import { state } from './state.js';

const listEl = document.querySelector('#suite-list');
const detailEl = document.querySelector('#detail');
const errorEl = document.querySelector('#error');
const ownerEl = document.querySelector('#owner-filter');
const statusEl = document.querySelector('#status-filter');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}

function renderList() {
  const rows = state.suites.map(s =>
    '<button class="suite-row ' + (s.id === state.selectedId ? 'selected' : '') + '" data-id="' + escapeHtml(s.id) + '">' +
      '<strong>' + escapeHtml(s.name) + '</strong>' +
      '<span>' + escapeHtml(s.owner) + ' · ' + escapeHtml(s.status) + ' · r' + s.revision + '</span>' +
    '</button>'
  ).join('');
  listEl.innerHTML = rows || '<p class="muted">No suites match the filters.</p>';
}

function renderDetail() {
  const s = state.selected;
  if (!s) {
    detailEl.innerHTML = '<p class="muted">Select an evaluation suite.</p>';
    return;
  }
  const runs = s.availableRuns.map(r =>
    '<li>' + escapeHtml(r.id) + ' — ' + escapeHtml(r.model) + ' — ' + escapeHtml(r.datasetVersion) + '</li>'
  ).join('');
  detailEl.innerHTML =
    '<h2>' + escapeHtml(s.name) + '</h2>' +
    '<dl>' +
      '<dt>Owner</dt><dd>' + escapeHtml(s.owner) + '</dd>' +
      '<dt>Status</dt><dd>' + escapeHtml(s.status) + '</dd>' +
      '<dt>Dataset</dt><dd>' + escapeHtml(s.datasetVersion) + '</dd>' +
      '<dt>Approved run</dt><dd>' + escapeHtml(s.approvedRunId) + '</dd>' +
      '<dt>Revision</dt><dd>' + s.revision + '</dd>' +
    '</dl>' +
    '<h3>Available runs</h3><ul>' + runs + '</ul>' +
    '<form id="note-form">' +
      '<label>Owner note<textarea id="note" maxlength="240">' + escapeHtml(s.note) + '</textarea></label>' +
      '<button type="submit">Save note</button>' +
    '</form>';
}

function render() {
  errorEl.textContent = state.error;
  renderList();
  renderDetail();
}

async function reloadList() {
  state.error = '';
  try {
    const body = await fetchSuites(state.filters);
    state.suites = body.suites;
    if (state.selectedId && !state.suites.some(s => s.id === state.selectedId)) {
      state.selectedId = null;
      state.selected = null;
    }
  } catch (error) {
    state.error = error.message;
  }
  render();
}

async function selectSuite(id) {
  state.error = '';
  try {
    const body = await fetchSuite(id);
    state.selectedId = id;
    state.selected = body.suite;
  } catch (error) {
    state.error = error.message;
  }
  render();
}

listEl.addEventListener('click', event => {
  const row = event.target.closest('[data-id]');
  if (row) selectSuite(row.dataset.id);
});

detailEl.addEventListener('submit', async event => {
  if (event.target.id !== 'note-form' || !state.selected) return;
  event.preventDefault();
  state.error = '';
  const note = document.querySelector('#note').value;
  try {
    const body = await saveNote(state.selected.id, note, state.selected.revision);
    state.selected = body.suite;
    await reloadList();
  } catch (error) {
    state.error = error.message;
    if (error.status === 409 && error.body && error.body.suite) state.selected = error.body.suite;
    render();
  }
});

ownerEl.addEventListener('change', () => {
  state.filters.owner = ownerEl.value;
  reloadList();
});
statusEl.addEventListener('change', () => {
  state.filters.status = statusEl.value;
  reloadList();
});

reloadList();
