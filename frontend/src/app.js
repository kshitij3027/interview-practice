import { api } from './api.js';
import { createStore } from './store.js';
import { renderAccountTable } from './accountTable.js';
import { renderAccountPanel } from './accountPanel.js';
import { renderSettlementPanel } from './settlementPanel.js';

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
    </div>
    ${renderSettlementPanel(state)}`;

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

  root.querySelector('#settlement-preview-form')?.addEventListener('submit', async event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const csvText = String(form.get('csvText') ?? '');
    store.set({ csvText, settlementBusy: true, settlementError: '', settlementCommitted: false });
    try {
      const preview = await api.previewSettlement(csvText);
      store.set({ preview });
    } catch (error) {
      store.set({ preview: null, settlementError: error.message });
    } finally {
      store.set({ settlementBusy: false });
    }
  });

  root.querySelector('#settlement-commit')?.addEventListener('click', async () => {
    const { preview } = store.get();
    if (!preview) return;
    store.set({ settlementBusy: true, settlementError: '' });
    try {
      const result = await api.commitSettlement(preview.preview_id);
      store.set({ preview: null, settlementCommitted: result.status });
      await refresh();
    } catch (error) {
      if (error.status === 409) {
        store.set({
          preview: null,
          settlementCommitted: false,
          settlementError: 'Preview is stale — re-submit CSV to get a fresh preview',
        });
      } else {
        store.set({ settlementError: error.message });
      }
    } finally {
      store.set({ settlementBusy: false });
    }
  });
}

store.subscribe(render);
render(store.get());
refresh().catch(error => store.set({ error: error.message }));
