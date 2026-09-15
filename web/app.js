import { api } from "./api.js";
import { state } from "./store.js";

const els = {
  statusFilter: document.querySelector("#status-filter"),
  list: document.querySelector("#campaign-list"),
  detail: document.querySelector("#campaign-detail"),
  error: document.querySelector("#error"),
};

function money(cents) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);
}

function render() {
  els.error.textContent = state.error || "";
  els.statusFilter.value = state.statusFilter;
  els.list.innerHTML = state.campaigns.map((campaign) => `
    <button class="campaign ${campaign.id === state.selectedId ? "selected" : ""}" data-id="${campaign.id}">
      <strong>${campaign.account_name}</strong>
      <span>${campaign.name}</span>
      <small>${campaign.status} · rev ${campaign.revision}</small>
    </button>
  `).join("");

  if (!state.selected) {
    els.detail.innerHTML = `<p class="muted">Select a campaign.</p>`;
    return;
  }

  const c = state.selected;
  const nextStatus = c.status === "active" ? "paused" : "active";
  const history = c.budget_changes.length
    ? c.budget_changes.map((change) => `<li>${change.effective_at}: ${money(change.daily_budget_cents)}/day</li>`).join("")
    : "<li>No budget changes</li>";
  els.detail.innerHTML = `
    <h2>${c.account_name} — ${c.name}</h2>
    <dl>
      <dt>Status</dt><dd>${c.status}</dd>
      <dt>Timezone</dt><dd>${c.timezone}</dd>
      <dt>Base daily budget</dt><dd>${money(c.daily_budget_cents)}</dd>
      <dt>Campaign revision</dt><dd>${c.revision}</dd>
      <dt>Dataset revision</dt><dd>${c.dataset_revision}</dd>
    </dl>
    <button id="toggle-status" ${state.savingStatus ? "disabled" : ""}>Set ${nextStatus}</button>
    <h3>Budget history</h3>
    <ul>${history}</ul>
  `;
  document.querySelector("#toggle-status")?.addEventListener("click", () => updateStatus(nextStatus));
}

async function loadList({ keepSelection = true } = {}) {
  state.loadingList = true;
  state.error = null;
  render();
  try {
    const result = await api.listCampaigns(state.statusFilter);
    state.campaigns = result.campaigns;
    state.datasetRevision = result.dataset_revision;
    const selectedStillVisible = state.campaigns.some((c) => c.id === state.selectedId);
    if (!keepSelection || !selectedStillVisible) {
      state.selectedId = state.campaigns[0]?.id || null;
    }
    if (state.selectedId) await loadDetail(state.selectedId);
    else state.selected = null;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loadingList = false;
    render();
  }
}

async function loadDetail(id) {
  state.loadingDetail = true;
  state.error = null;
  render();
  try {
    const detail = await api.getCampaign(id);
    if (state.selectedId === id) {
      state.selected = detail;
      state.datasetRevision = detail.dataset_revision;
    }
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loadingDetail = false;
    render();
  }
}

async function updateStatus(status) {
  if (!state.selected || state.savingStatus) return;
  const id = state.selected.id;
  const expectedRevision = state.selected.revision;
  state.savingStatus = true;
  state.error = null;
  render();
  try {
    const updated = await api.setStatus(id, status, expectedRevision);
    state.selected = updated;
    state.datasetRevision = updated.dataset_revision;
    await loadList({ keepSelection: true });
  } catch (error) {
    if (error.status === 409 && error.payload?.current) {
      state.selected = error.payload.current;
      state.datasetRevision = error.payload.current.dataset_revision;
    }
    state.error = error.message;
  } finally {
    state.savingStatus = false;
    render();
  }
}

els.statusFilter.addEventListener("change", async (event) => {
  state.statusFilter = event.target.value;
  await loadList({ keepSelection: true });
});

els.list.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-id]");
  if (!button) return;
  state.selectedId = button.dataset.id;
  await loadDetail(state.selectedId);
});

loadList({ keepSelection: false });
