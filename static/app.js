import {getFlag,listFlags,saveNote} from "./api.js";
const state={filters:{status:"",owner:""},flags:[],selectedId:null,selected:null,datasetRevision:null,busyNote:false};
const el={
 status:document.querySelector("#status-filter"),owner:document.querySelector("#owner-filter"),
 rows:document.querySelector("#flag-rows"),detail:document.querySelector("#detail"),
 rev:document.querySelector("#dataset-revision"),error:document.querySelector("#error")
};
el.status.addEventListener("change",()=>{state.filters.status=el.status.value;refreshList();});
el.owner.addEventListener("input",()=>{state.filters.owner=el.owner.value.trim();refreshList();});
async function refreshList(){
 try{
  clearError(); const p=await listFlags(state.filters); state.flags=p.flags; state.datasetRevision=p.datasetRevision;
  renderList();renderRevision();
  if(state.selectedId&&state.flags.some(f=>f.id===state.selectedId)) await selectFlag(state.selectedId);
  else if(state.selectedId){state.selectedId=null;state.selected=null;renderDetail();}
 }catch(e){showError(e.message);}
}
async function selectFlag(id){
 try{clearError();const p=await getFlag(id);state.selectedId=id;state.selected=p.flag;state.datasetRevision=p.datasetRevision;renderList();renderDetail();renderRevision();}
 catch(e){showError(e.message);}
}
function renderList(){
 el.rows.replaceChildren();
 for(const f of state.flags){
  const b=document.createElement("button");b.type="button";b.className=`flag-row${f.id===state.selectedId?" selected":""}`;
  b.textContent=`${f.key} — ${f.owner} — ${f.status} — r${f.revision}`;b.addEventListener("click",()=>selectFlag(f.id));el.rows.append(b);
 }
 if(!state.flags.length)el.rows.textContent="No flags match.";
}
function renderDetail(){
 el.detail.replaceChildren();
 if(!state.selected){el.detail.textContent="Select a flag.";return;}
 const f=state.selected;
 const h=document.createElement("h2");h.textContent=f.name;
 const meta=document.createElement("p");meta.textContent=`${f.key} · ${f.owner} · ${f.status} · revision ${f.revision}`;
 const t=document.createElement("h3");t.textContent="Published configuration";
 const pre=document.createElement("pre");pre.textContent=JSON.stringify(f.publishedConfig,null,2);
 const label=document.createElement("label");label.textContent="Operator note";
 const note=document.createElement("textarea");note.rows=4;note.maxLength=240;note.value=f.operatorNote;
 const save=document.createElement("button");save.type="button";save.textContent=state.busyNote?"Saving…":"Save note";save.disabled=state.busyNote;
 save.addEventListener("click",async()=>{
  if(state.busyNote)return; state.busyNote=true;
  try{clearError();const p=await saveNote(f.id,f.revision,note.value);state.selected=p.flag;state.datasetRevision=p.datasetRevision;await refreshList();}
  catch(e){if(e.status===409&&e.payload?.current)state.selected=e.payload.current;showError(e.message);}
  finally{state.busyNote=false;renderDetail();renderRevision();}
 });
 el.detail.append(h,meta,t,pre,label,note,save);
}
function renderRevision(){el.rev.textContent=state.datasetRevision??"—";}
function showError(m){el.error.textContent=m;el.error.hidden=false;}
function clearError(){el.error.textContent="";el.error.hidden=true;}
refreshList();
