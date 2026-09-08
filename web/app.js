import { api } from './api.js';
import { state, selectedShiftFromList } from './store.js';

const root = document.querySelector('#app');

function employeeName(id) {
  return state.employees.find((employee) => employee.id === id)?.name || id || 'Unassigned';
}

function render() {
  const selected = state.selectedShift || selectedShiftFromList();
  root.innerHTML = `
    <header>
      <div><h1>ShiftBoard</h1><p>Published workforce schedule</p></div>
      <label>Site
        <select id="site-filter">
          ${['all', 'SFO', 'OAK'].map((site) => `<option value="${site}" ${site === state.site ? 'selected' : ''}>${site}</option>`).join('')}
        </select>
      </label>
    </header>
    ${state.error ? `<div class="message error">${escapeHtml(state.error)}</div>` : ''}
    ${state.notice ? `<div class="message notice">${escapeHtml(state.notice)}</div>` : ''}
    <main>
      <section class="panel list-panel">
        <h2>Shifts</h2>
        ${state.loading ? '<p>Loading…</p>' : `<div class="shift-list">${state.shifts.map((shift) => `
          <button class="shift-row ${shift.id === state.selectedShiftId ? 'selected' : ''}" data-shift-id="${shift.id}">
            <strong>${shift.site} · ${shift.role}</strong>
            <span>${formatTime(shift.starts_at)}–${formatTime(shift.ends_at)}</span>
            <span>${escapeHtml(employeeName(shift.employee_id))} · rev ${shift.revision}</span>
          </button>`).join('')}</div>`}
      </section>
      <section class="panel detail-panel">
        ${selected ? detailMarkup(selected) : '<p>Select a shift.</p>'}
      </section>
    </main>`;

  document.querySelector('#site-filter')?.addEventListener('change', async (event) => {
    state.site = event.target.value;
    await loadShifts();
  });
  document.querySelectorAll('[data-shift-id]').forEach((button) => button.addEventListener('click', async () => {
    state.selectedShiftId = button.dataset.shiftId;
    await loadSelected();
  }));
  document.querySelector('#reassign-form')?.addEventListener('submit', saveAssignment);
}

function detailMarkup(shift) {
  const eligible = state.employees.filter((employee) => employee.sites.includes(shift.site) && employee.roles.includes(shift.role));
  return `
    <h2>${shift.site} ${shift.role}</h2>
    <dl>
      <dt>Shift</dt><dd>${shift.id}</dd>
      <dt>Starts</dt><dd>${formatTime(shift.starts_at)}</dd>
      <dt>Ends</dt><dd>${formatTime(shift.ends_at)}</dd>
      <dt>Revision</dt><dd>${shift.revision}</dd>
    </dl>
    <form id="reassign-form">
      <label>Assigned employee
        <select id="employee-select" ${state.saving ? 'disabled' : ''}>
          ${eligible.map((employee) => `<option value="${employee.id}" ${employee.id === shift.employee_id ? 'selected' : ''}>${escapeHtml(employee.name)}</option>`).join('')}
        </select>
      </label>
      <button ${state.saving ? 'disabled' : ''}>${state.saving ? 'Saving…' : 'Save assignment'}</button>
    </form>
    <p class="hint">Assignments reject stale revisions and overlapping employee shifts.</p>`;
}

async function saveAssignment(event) {
  event.preventDefault();
  const shift = state.selectedShift;
  if (!shift || state.saving) return;
  state.saving = true;
  state.error = '';
  state.notice = '';
  render();
  const employeeId = document.querySelector('#employee-select')?.value;
  try {
    const result = await api.reassign(shift.id, employeeId, shift.revision);
    state.notice = result.changed ? 'Assignment updated.' : 'Assignment already matches.';
    await loadShifts(false);
    await loadSelected(false);
  } catch (error) {
    state.error = error.message;
    if (error.status === 409 && error.details?.current_shift?.id === shift.id) {
      state.selectedShift = error.details.current_shift;
    }
  } finally {
    state.saving = false;
    render();
  }
}

async function loadShifts(showLoading = true) {
  if (showLoading) state.loading = true;
  state.error = '';
  render();
  try {
    const data = await api.shifts(state.site);
    state.shifts = data.shifts;
    if (state.selectedShiftId && !state.shifts.some((shift) => shift.id === state.selectedShiftId)) {
      state.selectedShiftId = null;
      state.selectedShift = null;
    }
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function loadSelected(renderAfter = true) {
  if (!state.selectedShiftId) return;
  try {
    const data = await api.shift(state.selectedShiftId);
    if (state.selectedShiftId === data.shift.id) state.selectedShift = data.shift;
  } catch (error) {
    state.error = error.message;
  }
  if (renderAfter) render();
}

function formatTime(value) {
  return new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

async function init() {
  try {
    const employees = await api.employees();
    state.employees = employees.employees;
    await loadShifts();
  } catch (error) {
    state.error = error.message;
    render();
  }
}

init();
