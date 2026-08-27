import {api} from './api.js';
import {state, mergeList, mergeDetail} from './store.js';

const accountsEl = document.querySelector('#accounts');
const detailEl = document.querySelector('#detail');
const segmentEl = document.querySelector('#segment');
const revisionEl = document.querySelector('#revision');
const errorEl = document.querySelector('#error');

async function loadAccounts() {
  try { mergeList(await api.listAccounts(state.segment)); state.error=''; render(); }
  catch (e) { state.error=e.message; render(); }
}
async function selectAccount(id) {
  state.selectedId=id;
  try { mergeDetail(await api.accountDetail(id)); state.error=''; render(); }
  catch (e) { state.error=e.message; render(); }
}
async function submitOverride(event) {
  event.preventDefault();
  if (!state.detail) return;
  const form = new FormData(event.currentTarget);
  const raw = form.get('classification');
  const payload = {classification: raw === 'clear' ? null : raw, reason:String(form.get('reason') || ''), expected_revision:state.detail.account.revision};
  try {
    const result = await api.setOverride(state.detail.account.id, payload);
    mergeDetail({...state.detail, account:result.account, dataset_revision:result.dataset_revision});
    state.error=''; render();
  } catch (e) {
    state.error=e.message;
    if (e.status === 409) await selectAccount(state.detail.account.id); else render();
  }
}
function render() {
  revisionEl.textContent=`Dataset revision ${state.datasetRevision}`;
  errorEl.textContent=state.error;
  accountsEl.innerHTML=state.accounts.map(a=>`<div class="row ${a.id===state.selectedId?'selected':''}" data-id="${a.id}"><strong>${a.name}</strong><div>${a.segment} · ${a.owner}</div><div>rev ${a.revision}${a.manual_override?` · override: ${a.manual_override.classification}`:''}</div></div>`).join('') || '<div class="muted">No accounts</div>';
  accountsEl.querySelectorAll('[data-id]').forEach(el=>el.addEventListener('click',()=>selectAccount(el.dataset.id)));
  if (!state.detail || state.detail.account.id !== state.selectedId) { detailEl.innerHTML='Select an account.'; return; }
  const {account, signals}=state.detail;
  detailEl.innerHTML=`<div class="card"><strong>${account.name}</strong><div>${account.segment} · renewal ${account.renewal_on}</div><div>Account revision ${account.revision}</div><p>Manual override: ${account.manual_override?`${account.manual_override.classification} — ${account.manual_override.reason}`:'none'}</p><form id="override" class="override"><select name="classification"><option value="healthy">healthy</option><option value="watch">watch</option><option value="critical">critical</option><option value="clear">clear override</option></select><input name="reason" placeholder="Reason"><button type="submit">Save override</button></form></div><h3>Raw signals</h3><div class="signals">${signals.map(s=>`<div class="row"><code>${s.metric}</code> = ${s.value}<br><span class="muted">${s.observed_at} · ${s.observation_id}</span></div>`).join('')}</div>`;
  document.querySelector('#override').addEventListener('submit', submitOverride);
}
segmentEl.addEventListener('change', async e=>{state.segment=e.target.value; await loadAccounts(); if(state.selectedId) await selectAccount(state.selectedId);});
loadAccounts();
