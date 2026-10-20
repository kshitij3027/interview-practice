const $ = (id) => document.getElementById(id);
const ui = { selectedId: null, current: null, listToken: 0, detailToken: 0 };

async function request(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { 'content-type': 'application/json', ...(options.headers || {}) } });
  let body;
  try { body = await response.json(); } catch { throw new Error('Invalid server response'); }
  if (!response.ok) throw new Error(body.error?.message || `HTTP ${response.status}`);
  return body;
}

function el(tag, text = '', className = '') {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

function renderDetail(shift) {
  $('details').replaceChildren();
  $('details').append(el('h3', `${shift.id} — ${shift.employee.name}`));
  for (const [label, value] of [
    ['Facility', shift.employee.facility], ['Status', shift.status], ['Start', shift.startAt],
    ['End', shift.endAt], ['Unpaid breaks', String(shift.breaks.length)],
    ['Paid minutes', String(shift.paidMinutes)], ['Revision', String(shift.revision)],
  ]) $('details').append(el('p', `${label}: ${value}`));
  const breaks = el('ul');
  for (const item of shift.breaks) breaks.append(el('li', `${item.startAt} – ${item.endAt}`));
  $('details').append(breaks);
  $('note').value = shift.note;
  $('noteForm').hidden = false;
  $('detailMessage').textContent = '';
}

async function loadDetail(id) {
  const token = ++ui.detailToken;
  if (!id) { $('details').replaceChildren(); $('noteForm').hidden = true; $('detailMessage').textContent = 'Select a shift.'; return; }
  $('detailMessage').textContent = 'Loading shift…';
  try {
    const data = await request(`/api/shifts/${encodeURIComponent(id)}`);
    if (token !== ui.detailToken || ui.selectedId !== id) return;
    ui.current = data.shift;
    renderDetail(data.shift);
  } catch (error) {
    if (token === ui.detailToken && ui.selectedId === id) $('detailMessage').textContent = error.message;
  }
}

async function loadList() {
  const token = ++ui.listToken;
  const params = new URLSearchParams({ employeeId: $('employee').value, status: $('status').value, q: $('query').value });
  $('listMessage').textContent = 'Loading…';
  try {
    const data = await request(`/api/shifts?${params}`);
    if (token !== ui.listToken) return;
    $('listMessage').textContent = '';
    $('count').textContent = `(${data.shifts.length})`;
    $('shiftList').replaceChildren();
    for (const shift of data.shifts) {
      const button = el('button', `${shift.id} · ${shift.employee.name} · ${shift.status} · ${shift.paidMinutes}m`, 'shift');
      button.addEventListener('click', () => { ui.selectedId = shift.id; loadDetail(shift.id); });
      $('shiftList').append(button);
    }
    if (ui.selectedId && !data.shifts.some((shift) => shift.id === ui.selectedId)) {
      ui.selectedId = null; ui.current = null; loadDetail(null);
    }
  } catch (error) { if (token === ui.listToken) $('listMessage').textContent = error.message; }
}

$('noteForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!ui.current) return;
  const id = ui.current.id;
  const revision = ui.current.revision;
  $('saveNote').disabled = true;
  $('detailMessage').textContent = 'Saving…';
  try {
    const response = await request(`/api/shifts/${encodeURIComponent(id)}/note`, {
      method: 'PATCH', body: JSON.stringify({ note: $('note').value, expectedRevision: revision }),
    });
    if (ui.selectedId === id && ui.current?.revision === revision) {
      ui.current = response.shift;
      renderDetail(response.shift);
    }
    loadList();
  } catch (error) {
    if (ui.selectedId === id) $('detailMessage').textContent = error.message;
  } finally { $('saveNote').disabled = false; }
});

for (const id of ['employee', 'status', 'query']) {
  $(id).addEventListener(id === 'query' ? 'input' : 'change', () => {
    ui.selectedId = null; ui.current = null; ++ui.detailToken; loadDetail(null); loadList();
  });
}

try {
  const data = await request('/api/employees');
  for (const employee of data.employees) {
    const option = el('option', employee.name);
    option.value = employee.id;
    $('employee').append(option);
  }
  loadList();
} catch (error) { $('listMessage').textContent = error.message; }
