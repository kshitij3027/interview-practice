import { api } from './api.js';
import { createStore } from './store.js';
import { classifyReport, nextRevision } from './reportGuards.js';

const store = createStore();
const app = document.querySelector('#app');

// Request bookkeeping lives outside the store: it is never rendered, so keeping it in state
// would trigger a re-render on every request.
let latestRequestId = 0;
let staleRetries = 0;
const MAX_STALE_RETRIES = 3;

// Every revision update goes through here, so the client's known revision is monotonic.
function applyRevision(incoming) {
  const revision = nextRevision(store.get().revision, incoming);
  if (revision !== store.get().revision) store.set({ revision });
}

function visibleUsers(state) {
  return state.selectedSegment === 'all'
    ? state.users
    : state.users.filter(user => user.segment === state.selectedSegment);
}

function formatRate(value) {
  // Backend already rounded to one decimal; toFixed here is presentation only.
  return value === null || value === undefined ? '—' : `${value.toFixed(1)}%`;
}

// Read from the report itself, never from current state: after an exclusion or a segment
// change the previous report stays visible until the new one lands, and labelling it with the
// newly selected segment would mislabel stale numbers as current.
function reportMeta(state) {
  const { report } = state;
  if (!report) return '';
  const parts = [`segment: ${report.segment}`, `revision ${report.revision}`];
  if (report.revision !== state.revision) parts.push(`updating to revision ${state.revision}…`);
  else if (report.segment !== state.selectedSegment) parts.push(`updating to ${state.selectedSegment}…`);
  else if (state.reportLoading) parts.push('updating…');
  return parts.join(' · ');
}

function renderReport(state) {
  const { report } = state;
  const error = state.reportError
    ? `<p class="report-error">Report failed: ${state.reportError}${report ? ' — showing the last successful report below.' : ''}</p>`
    : '';

  if (!report) {
    return `${error}<p class="report-empty">${state.reportLoading ? 'Loading report…' : 'No report yet.'}</p>`;
  }

  // Columns come from the response, so the backend stays the single source of funnel semantics.
  return `
    ${error}
    <table class="report">
      <thead><tr><th>Variant</th><th>Eligible</th>${report.steps.map(step => `<th>${step}</th>`).join('')}</tr></thead>
      <tbody>${Object.entries(report.variants).map(([variant, data]) => `
        <tr>
          <td>${variant}</td>
          <td>${data.eligible}</td>
          ${report.steps.map(step => `<td>${data.steps[step]} <span class="rate">(${formatRate(data.rates[step])})</span></td>`).join('')}
        </tr>`).join('')}</tbody>
    </table>
    <p class="report-note">Rates use the immediately preceding step as denominator; the first uses eligible users.</p>
  `;
}

function render(state) {
  const overview = state.overview;
  app.innerHTML = `
    <header><h1>Signal Lab</h1><p>Experiment operations dashboard</p></header>
    <section class="cards">
      <article><strong>Dataset revision</strong><span>${state.revision}</span></article>
      <article><strong>Assignments</strong><span>${overview?.assignment_count ?? '—'}</span></article>
      <article><strong>Raw events</strong><span>${overview?.raw_event_count ?? '—'}</span></article>
    </section>
    <section class="toolbar">
      <label>Segment
        <select id="segment">
          <option value="all" ${state.selectedSegment === 'all' ? 'selected' : ''}>All</option>
          <option value="self-serve" ${state.selectedSegment === 'self-serve' ? 'selected' : ''}>Self-serve</option>
          <option value="enterprise" ${state.selectedSegment === 'enterprise' ? 'selected' : ''}>Enterprise</option>
        </select>
      </label>
      <button id="refresh" ${state.loading ? 'disabled' : ''}>Refresh</button>
    </section>
    <p class="message">${state.message}</p>
    <table>
      <thead><tr><th>User</th><th>Variant</th><th>Segment</th><th>Assigned</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>${visibleUsers(state).map(user => `
        <tr>
          <td>${user.user_id}</td><td>${user.variant}</td><td>${user.segment}</td><td>${user.assigned_at}</td>
          <td>${user.excluded ? `Excluded: ${user.exclusion_reason}` : 'Included'}</td>
          <td>${user.excluded
            ? `<button data-include="${user.user_id}">Include</button>`
            : `<button data-exclude="${user.user_id}">Exclude</button>`}</td>
        </tr>`).join('')}</tbody>
    </table>
    <section class="placeholder">
      <div class="report-head">
        <h2>Analysis</h2>
        <span class="report-meta">${reportMeta(state)}</span>
      </div>
      <div class="report-controls">
        <label>Test delay (ms)
          <input id="delay" type="number" min="0" max="5000" step="100" value="${state.debugDelayMs}">
        </label>
        <button id="run-report" ${state.reportLoading ? 'disabled' : ''}>Run report</button>
      </div>
      ${renderReport(state)}
    </section>
  `;

  document.querySelector('#segment').addEventListener('change', event => selectSegment(event.target.value));
  document.querySelector('#refresh').addEventListener('click', refresh);
  // 'change' not 'input': the whole page re-renders on every state change, so committing per
  // keystroke would destroy focus mid-typing.
  document.querySelector('#delay').addEventListener('change', event => {
    store.set({ debugDelayMs: Math.max(0, Number(event.target.value) || 0) });
  });
  document.querySelector('#run-report').addEventListener('click', loadReport);
  document.querySelectorAll('[data-exclude]').forEach(button => button.addEventListener('click', () => exclude(button.dataset.exclude)));
  document.querySelectorAll('[data-include]').forEach(button => button.addEventListener('click', () => include(button.dataset.include)));
}

async function refresh() {
  store.set({ loading: true, message: '' });
  try {
    const [overview, users] = await Promise.all([api.overview(), api.users()]);
    store.set({ overview, users: users.users, loading: false });
    applyRevision(Math.max(overview.revision, users.revision));
  } catch (error) {
    store.set({ loading: false, message: error.message });
  }
}

// The one place the known revision may move backwards, and only on authoritative evidence:
// `overview` is never delayed, so a revision below ours there means the dataset itself was
// reset rather than that we are looking at an old response. Returns true if it resynced.
async function resyncRevision() {
  try {
    const overview = await api.overview();
    if (overview.revision >= store.get().revision) return false;
    store.set({ revision: overview.revision });
    await refresh();
    // Set after refresh(), which clears `message` as its first action.
    store.set({ message: 'Dataset revision went backwards — the API server appears to have restarted.' });
    return true;
  } catch {
    return false;
  }
}

async function loadReport() {
  const requestId = ++latestRequestId;
  const { selectedSegment: segment, debugDelayMs } = store.get();
  store.set({ reportLoading: true, reportError: '' });
  try {
    const response = await api.funnel(segment, debugDelayMs);
    // Classify BEFORE folding the response's revision into what we know, or the comparison
    // below becomes `n < n` and the staleness guard silently stops firing.
    const decision = classifyReport({
      requestId,
      latestRequestId,
      responseSegment: response.segment,
      selectedSegment: store.get().selectedSegment,
      responseRevision: response.revision,
      knownRevision: store.get().revision
    });

    // A newer request owns the UI now, including the loading flag — clearing it here would
    // flicker it off while that request is still running.
    if (decision === 'discard') return;

    if (decision === 'refetch') {
      if (staleRetries >= MAX_STALE_RETRIES) {
        staleRetries = 0;
        // A stale response is never rendered, whatever the retry count. Instead, ask an
        // authoritative endpoint what the current revision actually is: a persistent
        // regression means the dataset was reset (restarting the API clears exclusions and
        // restarts the counter), not that this response is trustworthy.
        if (await resyncRevision()) return loadReport();
        store.set({ reportLoading: false, reportError: 'the dataset kept changing; run the report again' });
        return;
      }
      staleRetries += 1;
      return loadReport();
    }

    staleRetries = 0;
    applyRevision(response.revision);
    store.set({ report: response, reportLoading: false, reportError: '' });
  } catch (error) {
    // A superseded failure must not paint an error over a newer successful report.
    if (requestId !== latestRequestId) return;
    // `report` is deliberately untouched: the last known-good report stays visible.
    store.set({ reportLoading: false, reportError: error.message });
  }
}

function selectSegment(segment) {
  store.set({ selectedSegment: segment });
  loadReport();
}

async function setExclusion(userId, excluded, reason) {
  try {
    const result = await api.setExclusion(userId, excluded, reason);
    // Applied before any further await: until the client knows the new revision, an in-flight
    // report response computed against the old dataset still looks current.
    applyRevision(result.revision);
    await refresh();
    await loadReport();
  } catch (error) {
    store.set({ message: error.message });
  }
}

function exclude(userId) {
  const reason = window.prompt('Reason for exclusion?');
  if (reason === null) return;
  return setExclusion(userId, true, reason);
}

function include(userId) {
  return setExclusion(userId, false);
}

store.subscribe(render);
render(store.get());
refresh().then(loadReport);
