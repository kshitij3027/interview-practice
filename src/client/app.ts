import type { Severity } from "../shared/types.js";
import { fetchIncident, fetchIncidents, updateSeverity } from "./api.js";
import { state } from "./store.js";

const root = document.querySelector<HTMLDivElement>("#app")!;

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]!));
}

function render(): void {
  const incident = state.selectedIncident;
  root.innerHTML = `
    <header><h1>Incident Desk</h1><span>Dataset rev ${state.datasetRevision}</span></header>
    <section class="toolbar">
      <label>Severity
        <select id="severity-filter">
          ${["all", "sev1", "sev2", "sev3"].map((value) => `<option value="${value}" ${state.severity === value ? "selected" : ""}>${value.toUpperCase()}</option>`).join("")}
        </select>
      </label>
      ${state.loadingList ? "<span>Refreshing…</span>" : ""}
      ${state.error ? `<span class="error">${escapeHtml(state.error)}</span>` : ""}
    </section>
    <main>
      <aside>
        ${state.incidents.map((item) => `
          <button class="incident-row ${state.selectedIncidentId === item.id ? "selected" : ""}" data-id="${item.id}">
            <strong>${escapeHtml(item.title)}</strong>
            <span>${item.severity.toUpperCase()} · ${item.status} · ${item.openActionCount} open actions</span>
          </button>`).join("") || "<p>No incidents</p>"}
      </aside>
      <section class="detail">
        ${state.loadingDetail ? "<p>Loading incident…</p>" : incident ? `
          <h2>${escapeHtml(incident.title)}</h2>
          <p>${incident.id} · ${incident.status} · started ${new Date(incident.startedAt).toLocaleString()}</p>
          <label>Severity
            <select id="severity-edit" ${state.savingSeverity ? "disabled" : ""}>
              ${["sev1", "sev2", "sev3"].map((value) => `<option value="${value}" ${incident.severity === value ? "selected" : ""}>${value.toUpperCase()}</option>`).join("")}
            </select>
          </label>
          <h3>Responders</h3>
          <p>${incident.responders.map(escapeHtml).join(", ")}</p>
          <h3>Action items</h3>
          <table>
            <thead><tr><th>Priority</th><th>Action</th><th>Owner</th><th>Due</th><th>Status</th><th>Rev</th></tr></thead>
            <tbody>${incident.actionItems.map((item) => `<tr>
              <td>${item.priority.toUpperCase()}</td>
              <td>${escapeHtml(item.summary)}</td>
              <td>${escapeHtml(item.owner ?? "Unassigned")}</td>
              <td>${item.dueAt ? new Date(item.dueAt).toLocaleString() : "—"}</td>
              <td>${item.status}</td>
              <td>${item.revision}</td>
            </tr>`).join("")}</tbody>
          </table>
        ` : "<p>Select an incident.</p>"}
      </section>
    </main>`;

  document.querySelector<HTMLSelectElement>("#severity-filter")?.addEventListener("change", async (event) => {
    state.severity = (event.target as HTMLSelectElement).value as Severity | "all";
    await loadList();
  });
  document.querySelectorAll<HTMLButtonElement>(".incident-row").forEach((button) => button.addEventListener("click", () => loadDetail(button.dataset.id!)));
  document.querySelector<HTMLSelectElement>("#severity-edit")?.addEventListener("change", async (event) => {
    if (!state.selectedIncident) return;
    const previous = state.selectedIncident.severity;
    const next = (event.target as HTMLSelectElement).value as Severity;
    if (previous === next) return;
    state.savingSeverity = true;
    state.error = null;
    render();
    try {
      const result = await updateSeverity(state.selectedIncident.id, next, state.selectedIncident.revision);
      state.selectedIncident = result.incident;
      state.datasetRevision = Math.max(state.datasetRevision, result.datasetRevision);
      await loadList(false);
    } catch (error) {
      state.error = (error as Error).message;
      await loadDetail(state.selectedIncident.id);
    } finally {
      state.savingSeverity = false;
      render();
    }
  });
}

async function loadList(renderLoading = true): Promise<void> {
  if (renderLoading) { state.loadingList = true; state.error = null; render(); }
  try {
    const result = await fetchIncidents(state.severity);
    state.incidents = result.incidents;
    state.datasetRevision = Math.max(state.datasetRevision, result.datasetRevision);
    if (state.selectedIncidentId && !result.incidents.some((item) => item.id === state.selectedIncidentId)) {
      state.selectedIncidentId = null;
      state.selectedIncident = null;
    }
  } catch (error) {
    state.error = (error as Error).message;
  } finally {
    state.loadingList = false;
    render();
  }
}

async function loadDetail(id: string): Promise<void> {
  state.selectedIncidentId = id;
  state.loadingDetail = true;
  state.error = null;
  render();
  try {
    const result = await fetchIncident(id);
    if (state.selectedIncidentId !== id) return;
    state.selectedIncident = result.incident;
    state.datasetRevision = Math.max(state.datasetRevision, result.datasetRevision);
  } catch (error) {
    if (state.selectedIncidentId === id) state.error = (error as Error).message;
  } finally {
    if (state.selectedIncidentId === id) state.loadingDetail = false;
    render();
  }
}

await loadList();
