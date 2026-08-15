import { api } from './api.js';
import { populateCohorts, initRollout, renderRollout } from './rollout.js';
import { state, visibleAccounts } from './store.js';

const $ = s => document.querySelector(s);

async function load({ preserveError = false } = {}) {
  if (!preserveError) state.error = '';
  try {
    const d = await api.loadAccounts();
    if (state.flag && d.flag.revision < state.flag.revision) return;
    Object.assign(state, { accounts: d.accounts, flag: d.flag, datasetRevision: d.datasetRevision });
    render();
  } catch (e) {
    state.error = e.message;
    render();
  }
}

async function loadCohorts() {
  try {
    const d = await api.loadCohorts();
    state.rollout.cohorts = d.cohorts;
    populateCohorts();
  } catch (e) {
    state.rollout.error = e.message;
    renderRollout();
  }
}

async function toggle(id, value) {
  if (state.busy) return;
  state.busy = id;
  state.error = '';
  render();
  try {
    await api.setOverride(id, value, state.flag.revision);
    await load();
  } catch (e) {
    state.error = e.status === 409 ? 'Flag changed. Refresh and try again.' : e.message;
    await load({ preserveError: true });
  } finally {
    state.busy = null;
    render();
  }
}

function render() {
  $('#meta').textContent = state.flag ? `Flag revision ${state.flag.revision} · dataset ${state.datasetRevision}` : 'Loading...';
  $('#error').textContent = state.error;
  $('#rows').innerHTML = visibleAccounts().map(a => `<tr><td>${a.name}</td><td>${a.plan}</td><td>${a.region}</td><td>${a.employees}</td><td>${a.override === null ? 'inherit' : String(a.override)}</td><td><button data-id="${a.id}" data-v="true" ${state.busy || state.rollout.busy === 'apply' ? 'disabled' : ''}>Enable</button> <button data-id="${a.id}" data-v="false" ${state.busy || state.rollout.busy === 'apply' ? 'disabled' : ''}>Disable</button></td></tr>`).join('');
  document.querySelectorAll('button[data-id]').forEach(b => b.onclick = () => toggle(b.dataset.id, b.dataset.v === 'true'));
  renderRollout();
}

$('#filter').onchange = e => {
  state.filter = e.target.value;
  render();
};
initRollout({ load, render });
load();
loadCohorts();
