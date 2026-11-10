import { api } from './api.js';
const el = id => document.getElementById(id);
const state = {org:'', id:'', detail:null, epoch:0};
const message = error => { el('error').textContent = error?.message || String(error); };
async function loadFlags() {
  const token = ++state.epoch, org = state.org;
  try {
    const data = await api.flags(org, el('search').value, el('status').value);
    if (token !== state.epoch || org !== state.org) return;
    el('total').textContent = `(${data.total})`;
    el('flags').replaceChildren(...data.flags.map(flag => {
      const button = document.createElement('button');
      button.textContent = `${flag.name} · ${flag.enabled ? 'on' : 'off'}`;
      button.classList.toggle('active', flag.id === state.id);
      button.onclick = () => selectFlag(flag.id);
      return button;
    }));
  } catch(error) { if (token === state.epoch) message(error); }
}
async function selectFlag(id) {
  state.id = id; state.detail = null;
  const token = ++state.epoch, org = state.org;
  el('detail').textContent = 'Loading…'; el('noteBox').hidden = true; el('noteFeedback').textContent = '';
  try {
    const detail = await api.detail(org,id);
    if (token !== state.epoch || org !== state.org || id !== state.id) return;
    state.detail = detail;
    const title = document.createElement('h2'); title.textContent = detail.name;
    const info = document.createElement('p'); info.textContent = `Feature: ${detail.id} · ${detail.enabled ? 'Enabled' : 'Disabled'} · Revision ${detail.revision}`;
    el('detail').replaceChildren(title,info);
    el('note').value = detail.note; el('noteBox').hidden = false;
    loadFlags();
  } catch(error) { if (token === state.epoch) message(error); }
}
async function loadOrganizations() {
  try { const orgs = await api.organizations();
    el('org').replaceChildren(...orgs.map(org => { const option = document.createElement('option'); option.value = org.id; option.textContent = org.name; return option; }));
    state.org = orgs[0]?.id || ''; if(state.org) await loadFlags();
  } catch(error) { message(error); }
}
el('org').addEventListener('change', () => {state.org=el('org').value;state.id='';state.detail=null;state.epoch++;el('detail').textContent='Select a feature.';el('noteBox').hidden=true;loadFlags();});
el('search').addEventListener('input', () => loadFlags());
el('status').addEventListener('change', () => loadFlags());
el('saveNote').onclick = async () => {
  const detail = state.detail; if (!detail) return;
  const org = state.org, id = state.id, token = state.epoch;
  el('noteFeedback').textContent = 'Saving…';
  try { const updated = await api.note(org,id,el('note').value,detail.revision);
    if (token !== state.epoch || id !== state.id || org !== state.org) return;
    state.detail=updated;el('noteFeedback').textContent=`Saved · revision ${updated.revision}`;loadFlags();
  } catch(error) { if(token === state.epoch) {el('noteFeedback').textContent=error.message; if(error.status === 409) selectFlag(id);} }
};
loadOrganizations();
