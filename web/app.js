import * as api from "./api.js";
import {createStore,upsertScreen} from "./store.js";
const state=createStore();
const listEl=document.querySelector("#screenList"),detailEl=document.querySelector("#detail"),errorEl=document.querySelector("#error");
const zoneEl=document.querySelector("#zoneFilter"),statusEl=document.querySelector("#statusFilter");

async function loadList(){
  state.loadingList=true;state.error="";render();
  try{const data=await api.listScreens(state.filters);state.screens=data.screens;state.datasetRevision=data.datasetRevision;
    if(state.selectedId&&!state.screens.some(s=>s.id===state.selectedId)){state.selectedId=null;state.detail=null;state.selectionToken++;}}
  catch(e){state.error=e.message;}finally{state.loadingList=false;render();}
}
async function selectScreen(id){
  state.selectedId=id;const token=++state.selectionToken;state.loadingDetail=true;state.error="";render();
  try{const data=await api.getScreen(id);if(token!==state.selectionToken||state.selectedId!==id)return;state.detail=data;state.datasetRevision=data.datasetRevision;}
  catch(e){if(token===state.selectionToken)state.error=e.message;}finally{if(token===state.selectionToken)state.loadingDetail=false;render();}
}
async function setMode(mode){
  if(!state.detail||state.savingMode)return;const screen=state.detail.screen;const selectedAtStart=state.selectedId;state.savingMode=true;state.error="";render();
  try{const data=await api.updateMode(screen.id,mode,screen.revision);if(state.selectedId===selectedAtStart)upsertScreen(state,data.screen);state.datasetRevision=data.datasetRevision;}
  catch(e){state.error=e.message;if(e.status===409&&e.data?.current&&state.selectedId===selectedAtStart){upsertScreen(state,e.data.current);state.datasetRevision=e.data.datasetRevision;}}
  finally{state.savingMode=false;render();}
}
function render(){
  errorEl.textContent=state.error;listEl.innerHTML="";
  if(state.loadingList&&state.screens.length===0)listEl.textContent="Loading…";
  for(const s of state.screens){const b=document.createElement("button");b.className="screen";b.innerHTML=`<strong>${esc(s.venue)}</strong><br><span class="muted">${s.zone} · ${s.status} · ${esc(s.baselinePlaylist)}</span>`;b.addEventListener("click",()=>selectScreen(s.id));listEl.appendChild(b);}
  if(!state.selectedId){detailEl.innerHTML='<span class="muted">Select a screen.</span>';return;}
  if(state.loadingDetail&&!state.detail){detailEl.textContent="Loading screen…";return;}
  const s=state.detail?.screen;if(!s||s.id!==state.selectedId)return;
  detailEl.innerHTML=`<h2>${esc(s.venue)} — ${s.zone}</h2>
  <div class="row"><span>ID</span><strong>${esc(s.id)}</strong></div>
  <div class="row"><span>Status</span><strong>${s.status}</strong></div>
  <div class="row"><span>Baseline playlist</span><strong>${esc(s.baselinePlaylist)}</strong></div>
  <div class="row"><span>Playback mode</span><strong>${s.playbackMode}</strong></div>
  <div class="row"><span>Screen revision</span><strong>${s.revision}</strong></div>
  <div class="row"><span>Dataset revision</span><strong>${state.datasetRevision??"—"}</strong></div>
  <div class="actions"><button id="normalBtn" ${state.savingMode?"disabled":""}>Normal</button><button id="mutedBtn" ${state.savingMode?"disabled":""}>Muted</button></div>`;
  detailEl.querySelector("#normalBtn").addEventListener("click",()=>setMode("normal"));
  detailEl.querySelector("#mutedBtn").addEventListener("click",()=>setMode("muted"));
}
function esc(v){return String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
zoneEl.addEventListener("change",()=>{state.filters.zone=zoneEl.value;loadList();});
statusEl.addEventListener("change",()=>{state.filters.status=statusEl.value;loadList();});
loadList();
