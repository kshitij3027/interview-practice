import { api } from './api.js';
import { state, setState } from './store.js';

const root = document.querySelector('#app');

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function planOptions(selected) {
  return state.plans.filter((p) => p.active).map((p) => `<option value="${esc(p.key)}" ${p.key === selected ? 'selected' : ''}>${esc(p.name)}</option>`).join('');
}

function render() {
  const selected = state.selectedAccount;
  root.innerHTML = `
    <header><h1>EntitleOps</h1><p>Business date: 2026-08-20</p></header>
    ${state.error ? `<div class="error">${esc(state.error)}</div>` : ''}
    <main>
      <section>
        <h2>Accounts</h2>
        <div class="accounts">${state.accounts.map((a) => `<button class="account ${selected?.id === a.id ? 'selected' : ''}" data-id="${esc(a.id)}"><strong>${esc(a.name)}</strong><span>${esc(a.current_plan_key)} · rev ${a.revision}</span></button>`).join('')}</div>
      </section>
      <section>
        ${selected ? `
          <h2>${esc(selected.name)}</h2>
          <p>Revision ${selected.revision} · current plan <strong>${esc(selected.current_plan_key)}</strong></p>
          <table><thead><tr><th>Start</th><th>End (exclusive)</th><th>Plan</th></tr></thead><tbody>
            ${selected.segments.map((s) => `<tr><td>${esc(s.start_on)}</td><td>${esc(s.end_on || 'open')}</td><td>${esc(s.plan_key)}</td></tr>`).join('')}
          </tbody></table>
          <form id="current-plan-form">
            <label>Change plan effective today <select name="plan_key">${planOptions(selected.current_plan_key)}</select></label>
            <button ${state.loading ? 'disabled' : ''}>Apply current plan change</button>
          </form>
        ` : '<p>Select an account.</p>'}
      </section>
    </main>`;

  root.querySelectorAll('.account').forEach((button) => button.addEventListener('click', () => selectAccount(button.dataset.id)));
  root.querySelector('#current-plan-form')?.addEventListener('submit', changeCurrentPlan);
}

async function selectAccount(id) {
  try {
    setState({ loading: true, error: '' });
    const payload = await api.account(id);
    setState({ selectedAccount: payload.account, loading: false });
  } catch (error) {
    setState({ loading: false, error: error.message });
  }
}

async function changeCurrentPlan(event) {
  event.preventDefault();
  const selected = state.selectedAccount;
  if (!selected) return;
  const form = new FormData(event.currentTarget);
  try {
    setState({ loading: true, error: '' });
    const payload = await api.changeCurrentPlan(selected.id, form.get('plan_key'), selected.revision);
    const accountsPayload = await api.accounts();
    setState({ selectedAccount: payload.account, accounts: accountsPayload.accounts, loading: false });
  } catch (error) {
    setState({ loading: false, error: error.status === 409 ? 'This account changed. Refresh it before retrying.' : error.message });
  }
}

async function boot() {
  try {
    const [accountsPayload, plansPayload] = await Promise.all([api.accounts(), api.plans()]);
    setState({ accounts: accountsPayload.accounts, plans: plansPayload.plans });
    if (accountsPayload.accounts[0]) await selectAccount(accountsPayload.accounts[0].id);
  } catch (error) {
    setState({ error: error.message });
  }
}

window.addEventListener('statechange', render);
render();
boot();
