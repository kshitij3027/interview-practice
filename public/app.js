import {api} from './api.js';
const $ = id => document.getElementById(id);
let selected = null, generation = 0, listGeneration = 0;
const site = () => $('site').value;
function message(s) { $('message').textContent = s; }
function cell(row, value) { const td = row.insertCell(); td.textContent = value; return td; }
async function list() {
  const token = ++listGeneration, s = site();
  try {
    const result = await api('/api/meters',{site:s,q:$('search').value});
    if (token !== listGeneration || s !== site()) return;
    $('meters').replaceChildren();
    for (const m of result.meters) {
      const b = document.createElement('button'); b.textContent = `${m.id} · ${m.name}`;
      b.onclick = () => open(m.id); $('meters').append(b);
    }
  } catch(e) { if (token === listGeneration) message(e.message); }
}
async function open(id) {
  selected = id; const token = ++generation, s = site();
  $('heading').textContent = 'Loading…'; $('readings').replaceChildren();
  try {
    const d = await api(`/api/meters/${id}`,{site:s});
    if (token !== generation || s !== site()) return;
    $('heading').textContent = `${d.meter.name} · rev ${d.revision}`;
    const table = document.createElement('table');
    const header = table.createTHead().insertRow();
    for(const label of ['Reading','UTC','Seq','Epoch','Wh','Review']) cell(header,label);
    const body = table.createTBody();
    for (const r of d.readings) {
      const row = body.insertRow();
      for(const v of [r.id,r.at,r.seq,r.epoch,r.wh]) cell(row,v);
      const b = document.createElement('button'); b.textContent = r.review;
      cell(row,'').append(b);
      b.onclick = async () => {
        b.disabled = true;
        try { await api(`/api/meters/${id}/readings/${r.id}/review`,{site:s},{expectedRevision:d.revision,review:r.review === 'accepted'?'rejected':'accepted'}); if(token === generation) message('Review saved'); }
        catch(e) { if(token === generation) message(e.message); }
        finally { if(token === generation && s === site()) open(id); }
      };
    }
    $('readings').append(table);
  } catch(e) { if(token === generation) message(e.message); }
}
$('site').onchange = () => { generation++; selected=null; $('heading').textContent='Choose a meter'; $('readings').replaceChildren(); message(''); list(); };
$('search').oninput = list;
try { for (const s of await api('/api/sites')) $('site').add(new Option(s.name,s.id)); await list(); } catch(e) { message(e.message); }
