import {getReps,getOpportunities,reassign} from './api.js';
import {state,currentCursor,resetPaging} from './store.js';

const $=s=>document.querySelector(s);
async function load(){ try{ const page=await getOpportunities({owner:state.owner,stage:state.stage,q:state.q,cursor:currentCursor()}); state.items=page.items; state.nextCursor=page.next_cursor||''; render(); }catch{ state.message='Could not load queue'; render(); } }
function render(){
  $('#message').textContent=state.message;
  $('#rows').innerHTML=state.items.map(o=>`<tr><td>${o.account}</td><td>${o.region}</td><td>${o.stage}</td><td>${repName(o.owner_id)}</td><td>${o.priority_score}</td><td>r${o.revision}</td><td><button data-id="${o.id}">Reassign</button></td></tr>`).join('');
  $('#prev').disabled=state.cursorStack.length<=1; $('#next').disabled=!state.nextCursor;
  document.querySelectorAll('button[data-id]').forEach(b=>b.onclick=()=>openReassign(b.dataset.id));
}
function repName(id){ return state.reps.find(r=>r.id===id)?.name||id; }
function openReassign(id){ state.selectedId=id; const o=state.items.find(x=>x.id===id); $('#modalTitle').textContent=`Reassign ${o.account}`; $('#target').innerHTML=state.reps.map(r=>`<option value="${r.id}">${r.name}</option>`).join(''); $('#dialog').showModal(); }
$('#save').onclick=async()=>{ const o=state.items.find(x=>x.id===state.selectedId); try{ await reassign(o.id,$('#target').value,o.revision); state.message='Reassigned'; $('#dialog').close(); await load(); }catch(e){ state.message=`Reassign failed: ${e.message}`; $('#dialog').close(); await load(); } };
$('#filters').onsubmit=e=>{e.preventDefault(); state.owner=$('#owner').value; state.stage=$('#stage').value; state.q=$('#q').value.trim(); resetPaging(); load();};
$('#next').onclick=()=>{ if(state.nextCursor){state.cursorStack.push(state.nextCursor);load();} };
$('#prev').onclick=()=>{ if(state.cursorStack.length>1){state.cursorStack.pop();load();} };
(async()=>{ state.reps=await getReps(); $('#owner').innerHTML='<option value="">All owners</option>'+state.reps.map(r=>`<option value="${r.id}">${r.name}</option>`).join(''); await load(); })();
