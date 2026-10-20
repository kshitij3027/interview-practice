import {api} from './api.js';
const el=id=>document.getElementById(id);
const state={tenant:'all',status:'all',q:'',selected:null,detail:null,listToken:0,detailToken:0};
const safe=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
function message(s,failed=false){el('message').textContent=s;el('message').className=failed?'error':''}
async function refreshList(){
  const token=++state.listToken;
  try {
    const payload=await api.cases({tenant:state.tenant,status:state.status,q:state.q});
    if(token!==state.listToken)return;
    el('cases').innerHTML=payload.items.map(c=>`<button class="case ${state.selected===c.id?'selected':''}" data-id="${safe(c.id)}"><strong>${safe(c.id)}</strong> — ${safe(c.subject)}<br><small>${safe(c.tenantId)} · ${safe(c.customerId)} · ${safe(c.status)} · ${safe(c.priority)} · v${c.revision}</small></button>`).join('')||'<p>No matching cases.</p>';
    el('cases').querySelectorAll('button[data-id]').forEach(b=>b.onclick=()=>select(b.dataset.id));
  } catch(e){if(token===state.listToken)message(e.message,true)}
}
async function select(id){
  state.selected=id;state.detail=null;el('detail').textContent='Loading…';
  refreshList(); await refreshDetail();
}
async function refreshDetail(){
  const id=state.selected, token=++state.detailToken;
  if(!id){el('detail').textContent='Select a case';return}
  try{
    const data=await api.detail(id);
    if(token!==state.detailToken||id!==state.selected)return;
    state.detail=data;
    const c=data.case;
    el('detail').innerHTML=`<h2>${safe(c.id)} — ${safe(c.subject)}</h2><p>${safe(c.tenantId)} / ${safe(c.customerId)} / ${safe(c.issueKey)}<br>Status: ${safe(c.status)} · Priority: ${safe(c.priority)} · Owner: ${safe(c.owner)} · Revision: ${c.revision}</p><p>Labels: ${safe(c.labels.join(', '))}<br>Due: ${safe(c.slaDueAt||'none')}</p><form id="note-form"><label>Operator note<textarea id="note" maxlength="300">${safe(c.note)}</textarea></label><button>Save note</button></form><h3>Activity (${data.activity.length})</h3><ol>${data.activity.map(a=>`<li><small>${safe(a.at)} ${safe(a.eventId)}</small><br>${safe(a.type)}: ${safe(a.body)}</li>`).join('')}</ol>`;
    el('note-form').onsubmit=saveNote;
  }catch(e){if(token===state.detailToken)message(e.message,true)}
}
async function saveNote(event){
  event.preventDefault();
  const id=state.selected, detail=state.detail;
  if(!detail)return;
  const note=el('note').value;
  try{
    const response=await api.note(id,{note,expectedRevision:detail.case.revision});
    if(id!==state.selected)return;
    message(response.changed?'Note updated':'No change');
    await Promise.all([refreshDetail(),refreshList()]);
  }catch(e){if(id===state.selected){message(e.message,true);if(e.code==='stale_revision')await refreshDetail()}}
}
for(const name of ['tenant','status','q'])el(name).addEventListener(name==='q'?'input':'change',event=>{state[name]=event.target.value;refreshList()});
refreshList();
