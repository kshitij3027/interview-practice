import { getCatalog, listJobs, getJob, saveNote } from './api.js';
import { state, selectAccount, selectJob, resetSelection, currentList, currentDetail } from './store.js';
const el = id => document.getElementById(id);
const statusLabel = state => ({ in_progress: 'In progress', waiting_customer: 'Waiting customer', resolved: 'Resolved' })[state] ?? state;
function message(id, text) { el(id).textContent = text; }
async function refreshList() {
  const epoch = ++state.listEpoch, account = state.account;
  message('list-message', 'Loading…');
  try {
    const response = await listJobs(account, state.search, state.status);
    if (!currentList(epoch, account)) return;
    state.jobs = response.jobs;
    message('list-message', `${response.total} matching work orders`);
    el('jobs').replaceChildren(...response.jobs.map(job => {
      const button = document.createElement('button'); button.className = 'job'; button.type = 'button';
      button.setAttribute('aria-pressed', String(job.id === state.selectedId));
      const name = document.createElement('strong'); name.textContent = `${job.id} · ${job.asset}`;
      const detail = document.createElement('small'); detail.textContent = `${statusLabel(job.status)} · ${job.priority} · ${job.summary}`;
      button.append(name, detail); button.onclick = () => showJob(job.id); return button;
    }));
  } catch (error) { if (currentList(epoch, account)) message('list-message', error.message); }
}
async function showJob(id) {
  selectJob(id); const epoch = ++state.detailEpoch, account = state.account;
  el('detail').hidden = true; message('detail-message', 'Loading work order…');
  try {
    const response = await getJob(account, id);
    if (!currentDetail(epoch, id, account)) return;
    state.detail = response;
    const job = response.job, site = response.site;
    el('job-name').textContent = `${job.id} · ${job.asset}`;
    el('job-status').textContent = statusLabel(job.status);
    el('job-meta').textContent = `Revision ${job.revision} · ${job.accountId}`;
    el('job-summary').textContent = job.summary;
    el('site-info').textContent = `${site.name} (${site.timeZone})`;
    el('opened').textContent = job.openedAt;
    el('priority').textContent = job.priority;
    el('note').value = job.note;
    message('note-message', ''); message('detail-message', ''); el('detail').hidden = false;
    for (const button of el('jobs').children) button.setAttribute('aria-pressed', String(button.textContent.startsWith(id + ' ·')));
  } catch (error) { if (currentDetail(epoch, id, account)) message('detail-message', error.message); }
}
el('account').addEventListener('change', event => { selectAccount(event.target.value); el('detail').hidden = true; message('detail-message', 'Select a work order.'); refreshList(); });
el('search').addEventListener('input', event => { state.search = event.target.value; refreshList(); });
el('status').addEventListener('change', event => { state.status = event.target.value; refreshList(); });
el('save-note').addEventListener('click', async () => {
  if (!state.detail) return;
  const account = state.account, id = state.selectedId, revision = state.detail.job.revision;
  const epoch = state.detailEpoch, button = el('save-note'); button.disabled = true;
  message('note-message', 'Saving…');
  try {
    const response = await saveNote(account, id, { note: el('note').value, expectedRevision: revision });
    if (!currentDetail(epoch, id, account)) return;
    state.detail.job = response.job;
    el('note').value = response.job.note;
    el('job-meta').textContent = `Revision ${response.job.revision} · ${account}`;
    message('note-message', response.unchanged ? 'No changes.' : 'Saved.');
    await refreshList();
  } catch (error) { if (currentDetail(epoch, id, account)) message('note-message', error.status === 409 ? 'Outdated note. Reload the work order.' : error.message); }
  finally { button.disabled = false; }
});
(async function init() {
  try {
    const response = await getCatalog(); state.accounts = response.accounts;
    el('account').replaceChildren(...response.accounts.map(account => { const option = document.createElement('option'); option.value = account.id; option.textContent = account.name; return option; }));
    if (response.accounts.length) { selectAccount(response.accounts[0].id); await refreshList(); }
  } catch (error) { message('list-message', error.message); }
})();
