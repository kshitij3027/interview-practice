import {listBins,getBin,saveNote} from './api.js';
const $=id=>document.getElementById(id);
let selected='',rev=0,listSeq=0,detailSeq=0,busy=false;
const filters={q:'',zone:'',status:''};
function notice(s){$('notice').textContent=s;$('notice').classList.add('show');setTimeout(()=>$('notice').classList.remove('show'),3000);}
async function refresh(){const t=++listSeq;try{const d=await listBins(filters);if(t!==listSeq)return;$('meta').textContent=d.total+' bins · v'+d.datasetRevision;$('list').replaceChildren(...d.items.map(b=>{const e=document.createElement('button');e.textContent=b.id+' · '+b.sku+' · '+b.onHand+' each';e.dataset.id=b.id;if(b.id===selected)e.className='active';return e;}));}catch(e){if(t===listSeq)notice(e.message);}}
async function open(id){selected=id;const t=++detailSeq;$('detail').textContent='Loading…';refresh();try{const d=await getBin(id);if(t!==detailSeq||id!==selected)return;show(d);}catch(e){if(t===detailSeq)notice(e.message);}}
function show(d){const b=d.bin;rev=b.revision;$('detail').replaceChildren();const title=document.createElement('h2');title.textContent=b.id+' · '+b.label;const meta=document.createElement('p');meta.textContent=b.sku+' | '+b.zone+' | '+b.onHand+' each | case '+b.caseSize+' | '+b.status+' | revision '+b.revision;const form=document.createElement('form'),area=document.createElement('textarea'),button=document.createElement('button');area.value=b.note;area.id='note';button.type='submit';button.textContent='Save note';form.append(area,button);form.onsubmit=async e=>{e.preventDefault();if(busy)return;busy=true;button.disabled=true;try{const next=await saveNote(b.id,b.revision,area.value);if(selected===b.id&&rev===b.revision)show(next);notice(next.changed?'Saved':'Unchanged');refresh();}catch(err){notice(err.message);if(selected===b.id&&err.current)show(err.current);}finally{busy=false;button.disabled=false;}};$('detail').append(title,meta,form);}
$('list').onclick=e=>{const b=e.target.closest('[data-id]');if(b)open(b.dataset.id);};
for(const id of ['q','zone','status'])$(id).oninput=()=>{filters.q=$('q').value;filters.zone=$('zone').value;filters.status=$('status').value;refresh();};
refresh();
