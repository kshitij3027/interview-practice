const byId = id => document.getElementById(id);
const state = {org: '', selectedId: '', offset: 0, total: 0, pageSize: 6, listEpoch: 0, detailEpoch: 0, activeCase: null};

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw Object.assign(new Error(data.error || ('HTTP ' + response.status)), {status: response.status, current: data.current});
  }
  return data;
}
function message(id, content, error = false) {
  const target = byId(id);
  target.textContent = content;
  target.classList.toggle('error', error);
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}
async function boot() {
  try {
    const organizations = await request('/api/organizations');
    const selector = byId('org');
    selector.replaceChildren();
    for (const org of organizations) {
      const opt = element('option', org.name);
      opt.value = org.id;
      selector.append(opt);
    }
    state.org = organizations[0] ? organizations[0].id : '';
    await loadList();
  } catch (error) { message('listMessage', error.message, true); }
}
async function loadList() {
  const token = ++state.listEpoch;
  const org = state.org;
  message('listMessage', 'Loading cases…');
  const q = new URLSearchParams({
    org, q: byId('query').value, status: byId('status').value,
    offset: String(state.offset), limit: String(state.pageSize)
  });
  try {
    const data = await request('/api/cases?' + q);
    if (token !== state.listEpoch || org !== state.org) return;
    state.total = data.total;
    const list = byId('cases');
    list.replaceChildren();
    for (const c of data.cases) {
      const button = element('button', undefined, 'item');
      button.classList.toggle('active', c.id === state.selectedId);
      button.dataset.id = c.id;
      button.append(element('strong', c.subject));
      button.append(element('span', c.id + ' · ' + c.status + ' · ' + c.priority + ' priority', 'sub'));
      button.addEventListener('click', () => selectCase(c.id));
      list.append(button);
    }
    if (!data.cases.length) list.append(element('p', 'No matching cases.'));
    byId('pageInfo').textContent = (data.total ? state.offset + 1 : 0) + '–'
      + Math.min(data.total, state.offset + state.pageSize) + ' of ' + data.total;
    byId('prev').disabled = state.offset === 0;
    byId('next').disabled = state.offset + state.pageSize >= data.total;
    message('listMessage', '');
  } catch (error) {
    if (token === state.listEpoch) message('listMessage', error.message, true);
  }
}
async function selectCase(id) {
  state.selectedId = id;
  state.activeCase = null;
  const token = ++state.detailEpoch;
  const org = state.org;
  byId('detail').replaceChildren();
  message('detailMessage', 'Loading case…');
  document.querySelectorAll('button[data-id]').forEach(btn => btn.classList.toggle('active', btn.dataset.id === id));
  try {
    const c = await request('/api/cases/' + encodeURIComponent(id) + '?org=' + encodeURIComponent(org));
    if (token !== state.detailEpoch || state.selectedId !== id || state.org !== org) return;
    state.activeCase = c;
    renderDetail(c);
    message('detailMessage', '');
  } catch (error) {
    if (token === state.detailEpoch) message('detailMessage', error.message, true);
  }
}
function renderDetail(c) {
  const container = byId('detail');
  container.replaceChildren(element('h3', c.subject));
  const meta = element('div', undefined, 'meta');
  for (const [label, value] of [
    ['Case', c.id], ['Customer', c.customerId], ['Status', c.status],
    ['Priority', c.priority], ['Revision', c.revision], ['Tags', c.tags.join(', ')]
  ]) {
    const block = element('div');
    block.append(element('b', label), document.createTextNode(String(value)));
    meta.append(block);
  }
  container.append(meta, element('h3', 'Activity'));
  const events = [...c.timeline].sort((a,b) => a.at.localeCompare(b.at) || a.id.localeCompare(b.id));
  for (const entry of events) {
    const item = element('div', undefined, 'entry');
    item.append(element('span', entry.at + ' · ' + entry.actor + ' · ' + entry.id, 'small'));
    item.append(element('p', entry.text));
    container.append(item);
  }
  container.append(element('h3', 'Internal note'));
  const form = element('form');
  form.id = 'noteForm';
  const textarea = element('textarea');
  textarea.id = 'noteValue';
  textarea.maxLength = 500;
  textarea.value = c.note;
  const button = element('button', 'Save note');
  button.type = 'submit';
  form.append(textarea, button);
  container.append(form);
  const label = element('p');
  label.id = 'noteMessage';
  label.setAttribute('role', 'status');
  container.append(label);
  form.addEventListener('submit', saveNote);
}
async function saveNote(event) {
  event.preventDefault();
  const c = state.activeCase;
  if (!c) return;
  const payload = {orgId: state.org, expectedRevision: c.revision, note: byId('noteValue').value};
  const org = state.org, id = c.id;
  const button = byId('noteForm').querySelector('button');
  button.disabled = true;
  try {
    const updated = await request('/api/cases/' + encodeURIComponent(id) + '/note', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    if (state.org === org && state.selectedId === id) {
      state.activeCase = updated;
      renderDetail(updated);
      byId('noteMessage').textContent = 'Note saved.';
      loadList();
    }
  } catch (error) {
    if (state.org === org && state.selectedId === id) {
      byId('noteMessage').textContent = error.message;
      if (error.status === 409) {
        await selectCase(id);
        message('detailMessage', 'Case changed elsewhere; review current values.', true);
      }
    }
  } finally {
    if (state.org === org && state.selectedId === id && document.body.contains(button)) button.disabled = false;
  }
}
byId('org').addEventListener('change', () => {
  state.org = byId('org').value; state.selectedId = ''; state.activeCase = null;
  state.detailEpoch++; state.offset = 0;
  byId('detail').replaceChildren();
  message('detailMessage', 'Select a case.');
  loadList();
});
byId('query').addEventListener('input', () => {state.offset = 0; loadList();});
byId('status').addEventListener('change', () => {state.offset = 0; loadList();});
byId('prev').addEventListener('click', () => {state.offset = Math.max(0, state.offset - state.pageSize); loadList();});
byId('next').addEventListener('click', () => {state.offset += state.pageSize; loadList();});
boot();
