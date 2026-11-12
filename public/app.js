const $ = id => document.getElementById(id);
let org = '', selected = '', detail = null, offset = 0, total = 0;
let listEpoch = 0, detailEpoch = 0;
const pageSize = 6;
async function api(url, options = {}) {
  const response = await fetch(url, {headers: {'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error(data.error || ('HTTP ' + response.status)), {status:response.status, data});
  return data;
}
function node(tag, text, cls) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = String(text);
  if (cls) result.className = cls;
  return result;
}
async function loadList() {
  const epoch = ++listEpoch;
  const params = new URLSearchParams({org,q:$('search').value,status:$('status').value,offset:String(offset),limit:String(pageSize)});
  try {
    const result = await api('/api/contracts?' + params);
    if (epoch !== listEpoch) return;
    total = result.total;
    $('count').textContent = total + ' contracts';
    $('page').textContent = (total ? offset + 1 : 0) + '–' + Math.min(total,offset+pageSize) + ' of ' + total;
    $('previous').disabled = offset === 0;
    $('next').disabled = offset + pageSize >= total;
    $('list').replaceChildren();
    for (const c of result.contracts) {
      const button = node('button', c.customer, 'contract' + (c.id === selected ? ' selected' : ''));
      button.append(node('small',c.id + ' · ' + c.plan.name + ' · ' + c.status + ' · ' + c.seats + ' seats'));
      button.onclick = () => selectContract(c.id);
      $('list').append(button);
    }
    if (!result.contracts.length) $('list').append(node('p','No matching contracts.'));
  } catch(err) { if (epoch === listEpoch) $('count').textContent = err.message; }
}
async function selectContract(id) {
  selected = id;
  const epoch = ++detailEpoch;
  $('details').textContent = 'Loading…';
  $('notes').hidden = true;
  $('message').textContent = '';
  loadList();
  try {
    const result = await api('/api/contracts/' + encodeURIComponent(id) + '?org=' + encodeURIComponent(org));
    if (epoch !== detailEpoch) return;
    detail = result;
    renderDetail();
  } catch(err) { if (epoch === detailEpoch) $('details').textContent = err.message; }
}
function renderDetail() {
  if (!detail) return;
  const c = detail;
  const rows = [
    ['Customer',c.customer],['Contract',c.id],['Status',c.status],['Plan',c.plan.name],
    ['Monthly seat price','$' + (c.plan.seatPriceCents/100).toFixed(2)],['Current seats',c.seats],
    ['Billing period',c.periodStart + ' to ' + c.periodEnd + ' (end exclusive)'],
    ['Revision',c.revision],['Recorded seat changes',c.changes.length]
  ];
  const dl = node('dl');
  for (const [name,value] of rows) { dl.append(node('dt',name),node('dd',value)); }
  $('details').replaceChildren(dl);
  $('note').value = c.note;
  $('notes').hidden = false;
}
$('notes').onsubmit = async event => {
  event.preventDefault();
  if (!detail) return;
  const id = detail.id, revision = detail.revision, epoch = detailEpoch;
  const currentOrg = org;
  $('message').textContent = 'Saving…';
  try {
    const result = await api('/api/contracts/' + encodeURIComponent(id) + '/note',
      {method:'PATCH',body:JSON.stringify({orgId:currentOrg,expectedRevision:revision,note:$('note').value})});
    if (epoch !== detailEpoch) return;
    detail = result;
    renderDetail();
    loadList();
    $('message').textContent = 'Note saved.';
  } catch(err) {
    if (epoch !== detailEpoch) return;
    if (err.status === 409) await selectContract(id);
    $('message').textContent = err.status === 409 ? 'Contract changed. Reloaded current version.' : err.message;
  }
};
$('org').onchange = () => {
  org = $('org').value; offset = 0; selected = ''; detail = null; ++detailEpoch;
  $('details').textContent = 'Select a contract.';
  $('notes').hidden = true;
  $('message').textContent = '';
  loadList();
};
for (const id of ['search','status']) $(id).addEventListener(id === 'search' ? 'input' : 'change',()=>{offset=0;loadList();});
$('previous').onclick=()=>{offset=Math.max(0,offset-pageSize);loadList();};
$('next').onclick=()=>{offset+=pageSize;loadList();};
try {
  const catalog = await api('/api/catalog');
  $('org').replaceChildren();
  for (const o of catalog.organizations) {
    const option = node('option',o.name); option.value=o.id; $('org').append(option);
  }
  org = catalog.organizations[0].id;
  loadList();
} catch(err) { $('count').textContent = err.message; }
