const $ = (id) => document.getElementById(id);
const state = { selected: null, detail: null, listToken: 0, detailToken: 0, noteBusy: false };
const safeText = (value) => String(value ?? '');
const money = (cents) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100);

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}
function el(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = safeText(text);
  if (className) node.className = className;
  return node;
}

async function loadOrders() {
  const token = ++state.listToken;
  const params = new URLSearchParams({ search: $('search').value, status: $('status').value });
  $('listStatus').textContent = 'Loading orders…';
  try {
    const data = await api(`/api/orders?${params}`);
    if (token !== state.listToken) return;
    $('orders').replaceChildren();
    for (const order of data.orders) {
      const button = el('button', `${order.id} · ${order.customer} · ${order.status}`, 'order');
      button.type = 'button'; button.setAttribute('aria-pressed', String(order.id === state.selected));
      button.addEventListener('click', () => selectOrder(order.id));
      $('orders').append(button);
    }
    $('listStatus').textContent = `${data.orders.length} orders · dataset r${data.datasetRevision}`;
  } catch (error) {
    if (token === state.listToken) $('listStatus').textContent = `List unavailable: ${error.message}`;
  }
}

async function selectOrder(id) {
  state.selected = id;
  state.detail = null;
  const token = ++state.detailToken;
  $('detailStatus').textContent = 'Loading order…';
  $('detail').replaceChildren();
  await loadDetail(id, token);
  for (const node of $('orders').querySelectorAll('button')) node.setAttribute('aria-pressed', String(node.textContent.startsWith(id + ' ')));
}

async function loadDetail(id, token = ++state.detailToken) {
  try {
    const data = await api(`/api/orders/${encodeURIComponent(id)}`);
    if (token !== state.detailToken || state.selected !== id) return;
    state.detail = data;
    drawDetail();
  } catch (error) {
    if (token === state.detailToken && state.selected === id) $('detailStatus').textContent = `Detail unavailable: ${error.message}`;
  }
}

function drawDetail() {
  const { order, datasetRevision } = state.detail;
  $('detailStatus').textContent = `${order.id} · ${order.status} · order r${order.revision} · dataset r${datasetRevision}`;
  const view = $('detail'); view.replaceChildren();
  view.append(el('h3', order.customer), el('p', `Placed ${new Date(order.placedAt).toLocaleString()} · Shipping ${money(order.shippingCents)}`, 'muted'));
  const table = document.createElement('table');
  const head = document.createElement('tr');
  for (const col of ['Item', 'Ordered', 'Already refunded']) head.append(el('th', col));
  table.append(head);
  for (const line of order.lines) {
    const row = document.createElement('tr');
    for (const value of [`${line.label} (${line.sku})`, line.quantity, `${line.refundedQuantity} · ${money(line.refundedCents)}`]) row.append(el('td', value));
    table.append(row);
  }
  view.append(table, el('h3', 'Refund history'));
  if (!order.refunds.length) view.append(el('p', 'No refunds recorded.', 'muted'));
  for (const refund of order.refunds) view.append(el('p', `${refund.id}: ${money(refund.totalCents)} · ${refund.reason}`));
  const form = document.createElement('form');
  form.append(el('h3', 'Operator note'));
  const input = document.createElement('textarea'); input.name = 'note'; input.value = order.note; input.setAttribute('aria-label', 'Operator note');
  const submit = el('button', 'Save note'); submit.type = 'submit'; submit.disabled = state.noteBusy;
  const message = el('p', ''); form.append(input, submit, message);
  form.addEventListener('submit', async (event) => {
    event.preventDefault(); if (state.noteBusy) return;
    const id = order.id; const token = state.detailToken; state.noteBusy = true; submit.disabled = true;
    try {
      const data = await api(`/api/orders/${encodeURIComponent(id)}/note`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ expectedRevision: order.revision, note: input.value }) });
      if (state.selected !== id || token !== state.detailToken) return;
      state.detail = data; drawDetail(); void loadOrders();
    } catch (error) {
      if (state.selected === id && token === state.detailToken) { message.textContent = error.message; message.className = 'error'; }
    } finally { state.noteBusy = false; submit.disabled = false; }
  });
  view.append(form);
}

$('filters').addEventListener('submit', (event) => { event.preventDefault(); void loadOrders(); });
void loadOrders();
