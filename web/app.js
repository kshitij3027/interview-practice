import { api } from './api.js';
import { createStore } from './store.js';

const store = createStore();
const app = document.querySelector('#app');

function visibleUsers(state) {
  return state.selectedSegment === 'all'
    ? state.users
    : state.users.filter(user => user.segment === state.selectedSegment);
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
    <section class="placeholder"><h2>Analysis</h2><p>No funnel report has been configured for this dashboard.</p></section>
  `;

  document.querySelector('#segment').addEventListener('change', event => store.set({ selectedSegment: event.target.value }));
  document.querySelector('#refresh').addEventListener('click', refresh);
  document.querySelectorAll('[data-exclude]').forEach(button => button.addEventListener('click', () => exclude(button.dataset.exclude)));
  document.querySelectorAll('[data-include]').forEach(button => button.addEventListener('click', () => include(button.dataset.include)));
}

async function refresh() {
  store.set({ loading: true, message: '' });
  try {
    const [overview, users] = await Promise.all([api.overview(), api.users()]);
    store.set({ overview, users: users.users, revision: Math.max(overview.revision, users.revision), loading: false });
  } catch (error) {
    store.set({ loading: false, message: error.message });
  }
}

async function exclude(userId) {
  const reason = window.prompt('Reason for exclusion?');
  if (reason === null) return;
  try {
    await api.setExclusion(userId, true, reason);
    await refresh();
  } catch (error) {
    store.set({ message: error.message });
  }
}

async function include(userId) {
  try {
    await api.setExclusion(userId, false);
    await refresh();
  } catch (error) {
    store.set({ message: error.message });
  }
}

store.subscribe(render);
render(store.get());
refresh();
