const state = {
  meta: null,
  filters: { status: "all", system: "all", risk: "all" },
  cursor: null,
  history: [],
  page: null,
  selectedId: null,
  requestToken: 0,
};

const el = (id) => document.getElementById(id);

async function api(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || `HTTP ${response.status}`);
    error.body = body;
    error.status = response.status;
    throw error;
  }
  return body;
}

function setError(message = "") { el("error").textContent = message; }

async function loadMeta() {
  state.meta = await api("/api/meta");
  el("revision").textContent = `dataset r${state.meta.datasetRevision}`;
  for (const system of state.meta.systems) {
    const option = document.createElement("option");
    option.value = option.textContent = system;
    el("system").append(option);
  }
}

function listUrl(cursor) {
  const q = new URLSearchParams({ ...state.filters, limit: "4" });
  if (cursor) q.set("cursor", cursor);
  return `/api/grants?${q}`;
}

async function loadPage(cursor = null, { pushHistory = false } = {}) {
  const token = ++state.requestToken;
  setError();
  try {
    const page = await api(listUrl(cursor));
    if (token !== state.requestToken) return;
    if (pushHistory) state.history.push(state.cursor);
    state.cursor = cursor;
    state.page = page;
    renderList();
    el("revision").textContent = `dataset r${page.datasetRevision}`;
    if (state.selectedId && !page.items.some((g) => g.id === state.selectedId)) renderDetail(null);
  } catch (error) {
    if (token === state.requestToken) setError(error.message);
  }
}

function renderList() {
  const root = el("list");
  root.replaceChildren();
  for (const grant of state.page.items) {
    const button = document.createElement("button");
    button.className = `grant-row ${grant.id === state.selectedId ? "selected" : ""}`;
    button.innerHTML = `<strong>${grant.principal}</strong><span>${grant.system} · ${grant.role}</span><span>${grant.risk} · ${grant.status} · r${grant.revision}</span>`;
    button.addEventListener("click", () => selectGrant(grant.id));
    root.append(button);
  }
  el("page-summary").textContent = `${state.page.items.length} shown · ${state.page.total} matching`;
  el("prev").disabled = state.history.length === 0;
  el("next").disabled = !state.page.nextCursor;
}

async function selectGrant(id) {
  state.selectedId = id;
  renderList();
  setError();
  try {
    const body = await api(`/api/grants/${encodeURIComponent(id)}`);
    if (state.selectedId !== id) return;
    renderDetail(body.grant);
    el("revision").textContent = `dataset r${body.datasetRevision}`;
  } catch (error) { setError(error.message); }
}

function renderDetail(grant) {
  const root = el("detail");
  if (!grant) {
    state.selectedId = null;
    root.innerHTML = "<p>Select a grant.</p>";
    return;
  }
  root.innerHTML = `
    <h2>${grant.principal}</h2>
    <dl>
      <dt>System</dt><dd>${grant.system}</dd><dt>Role</dt><dd>${grant.role}</dd>
      <dt>Risk</dt><dd>${grant.risk}</dd><dt>Status</dt><dd>${grant.status}</dd>
      <dt>Last used</dt><dd>${grant.lastUsedAt ?? "never"}</dd><dt>Expires</dt><dd>${grant.expiresAt}</dd>
      <dt>Exception until</dt><dd>${grant.exceptionUntil ?? "none"}</dd><dt>Revision</dt><dd>${grant.revision}</dd>
    </dl>
    <form id="note-form">
      <label>Owner note <textarea id="note" maxlength="200">${grant.ownerNote}</textarea></label>
      <button>Save note</button>
    </form>`;
  el("note-form").addEventListener("submit", (event) => saveNote(event, grant));
}

async function saveNote(event, grant) {
  event.preventDefault();
  setError();
  try {
    const result = await api(`/api/grants/${grant.id}/note`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ expected_revision: grant.revision, note: el("note").value }),
    });
    renderDetail(result.grant);
    await loadPage(state.cursor);
  } catch (error) {
    if (error.status === 409 && error.body?.grant) renderDetail(error.body.grant);
    setError(error.message);
  }
}

el("apply-filters").addEventListener("click", () => {
  state.filters = { status: el("status").value, system: el("system").value, risk: el("risk").value };
  state.history = [];
  state.selectedId = null;
  renderDetail(null);
  loadPage(null);
});
el("next").addEventListener("click", () => state.page?.nextCursor && loadPage(state.page.nextCursor, { pushHistory: true }));
el("prev").addEventListener("click", () => {
  if (!state.history.length) return;
  const previous = state.history.pop();
  loadPage(previous);
});

await loadMeta();
await loadPage();
