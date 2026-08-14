import { api } from './api.js';
import { createStore } from './store.js';
import { renderAccountTable } from './accountTable.js';
import { renderAccountPanel } from './accountPanel.js';

const root = document.querySelector('#app');
const store = createStore();

async function loadAccounts() {
  const accounts = await api.accounts();
  const selectedId = store.get().selectedId ?? accounts[0]?.id ?? null;
  store.set({ accounts, selectedId });
}

async function loadDetail(id) {
  store.set({ detail: await api.account(id) });
}

async function refresh() {
  await loadAccounts();
  if (store.get().selectedId) await loadDetail(store.get().selectedId);
}

function render(state) {
  root.innerHTML = `
    <header><h1>Ledger Lens</h1><p>Customer balance and invoice operations</p></header>
    ${state.error ? `<p class="error">${state.error}</p>` : ''}
    <div class="layout">
      ${renderAccountTable(state.accounts, state.selectedId)}
      ${renderAccountPanel(state.detail, state.creditBusy)}
    </div>`;

  root.querySelectorAll('[data-account-id]').forEach(row => row.addEventListener('click', async () => {
    const id = row.dataset.accountId;
    store.set({ selectedId: id, error: '' });
    try { await loadDetail(id); } catch (error) { store.set({ error: error.message }); }
  }));

  root.querySelector('#credit-form')?.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const amountCents = Math.round(Number(form.get('amount')) * 100);
    const reason = String(form.get('reason') ?? '');
    store.set({ creditBusy: true, error: '' });
    try {
      await api.addCredit(store.get().selectedId, amountCents, reason);
      await refresh();
    } catch (error) {
      store.set({ error: error.message });
    } finally {
      store.set({ creditBusy: false });
    }
  });
}

store.subscribe(render);
render(store.get());
refresh().catch(error => store.set({ error: error.message }));
