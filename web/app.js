import { getCustomer, listCustomers, setCustomerStatus } from "./api.js";
import { state, setDetail, setList } from "./store.js";

const customersEl = document.querySelector("#customers");
const detailEl = document.querySelector("#detail");
const segmentEl = document.querySelector("#segment");
const revisionEl = document.querySelector("#dataset-revision");
const errorEl = document.querySelector("#error");

async function refreshList() {
  state.error = "";
  try {
    setList(await listCustomers(state.segment));
  } catch (error) {
    state.error = error.message;
  }
  render();
}

async function selectCustomer(id) {
  state.error = "";
  try {
    setDetail(await getCustomer(id));
  } catch (error) {
    state.error = error.message;
  }
  render();
}

async function updateStatus(status) {
  if (!state.detail || state.busy) return;
  state.busy = true;
  state.error = "";
  render();
  try {
    const result = await setCustomerStatus(state.detail.id, status, state.detail.revision);
    setDetail(result);
    await refreshList();
  } catch (error) {
    state.error = error.status === 409 ? "This profile changed. Reload the profile and try again." : error.message;
  } finally {
    state.busy = false;
    render();
  }
}

function renderCustomers() {
  customersEl.innerHTML = "";
  for (const customer of state.customers) {
    const button = document.createElement("button");
    button.className = `customer-row${customer.id === state.selectedId ? " selected" : ""}`;
    button.innerHTML = `<strong>${escapeHtml(customer.name)}</strong><span>${escapeHtml(customer.segment)} · ${escapeHtml(customer.status)} · r${customer.revision}</span>`;
    button.addEventListener("click", () => selectCustomer(customer.id));
    customersEl.appendChild(button);
  }
}

function renderDetail() {
  if (!state.detail) {
    detailEl.className = "panel muted";
    detailEl.textContent = "Select a customer.";
    return;
  }
  const c = state.detail;
  const tags = c.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join(" ");
  const activities = c.activities.map(a => `<li><strong>${escapeHtml(a.type)}</strong> ${escapeHtml(a.occurred_at)} — ${escapeHtml(a.summary)}</li>`).join("");
  detailEl.className = "panel";
  detailEl.innerHTML = `
    <h3>${escapeHtml(c.name)}</h3>
    <p>ID: <code>${escapeHtml(c.id)}</code> · revision ${c.revision}</p>
    <p>${tags}</p>
    <label>Status
      <select id="status-select" ${state.busy ? "disabled" : ""}>
        ${["prospect","active","paused"].map(s => `<option ${s === c.status ? "selected" : ""}>${s}</option>`).join("")}
      </select>
    </label>
    <h4>External IDs</h4><pre>${escapeHtml(JSON.stringify(c.external_ids, null, 2))}</pre>
    <h4>Fields</h4><pre>${escapeHtml(JSON.stringify(c.fields, null, 2))}</pre>
    <h4>Activity</h4><ul>${activities}</ul>`;
  document.querySelector("#status-select").addEventListener("change", e => updateStatus(e.target.value));
}

function render() {
  revisionEl.textContent = state.datasetRevision == null ? "" : `Dataset revision ${state.datasetRevision}`;
  errorEl.textContent = state.error;
  renderCustomers();
  renderDetail();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#039;",'"':"&quot;"}[ch]));
}

segmentEl.addEventListener("change", async event => {
  state.segment = event.target.value;
  await refreshList();
});

refreshList();
