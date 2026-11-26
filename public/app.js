import * as api from './api.js';
const $ = id => document.getElementById(id);
let current = null, generation = 0, selected = null, busy = false;
function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
function message(text){$('message').textContent=text;}
async function loadList(){const rows=await api.list();$('list').replaceChildren(...rows.map(r=>{const b=el('button',`${r.id} · ${r.asset} · v${r.version}`);b.onclick=()=>select(r.id);return b;}));}
async function select(id){const token=++generation;selected=id;current=null;busy=false;message('Loading…');$('detail').textContent='Loading…';try{const r=await api.detail(id);if(token!==generation)return;current=r;message('');render();}catch(e){if(token===generation)message(e.message);}}
function render(){const r=current;if(!r)return;const root=$('detail');root.replaceChildren(el('h2',r.asset),el('p',`${r.templateName} · v${r.version} · ${r.status} · revision ${r.revision}`));
for(const f of r.fields){const row=el('article');row.append(el('label',f.label+(f.required?' *':'')));const value=r.answers[f.id];let input;
if(f.type==='boolean'||f.type==='choice'){input=el('select');const choices=f.type==='boolean'?['true','false']:f.choices;for(const c of ['',...choices]){const o=el('option',c===''?'Not answered':c);o.value=c;input.append(o);}input.value=value===undefined?'':String(value);}else{input=el('input');input.type=f.type==='integer'?'number':'text';input.value=value??'';if(f.min!==undefined)input.min=f.min;if(f.max!==undefined)input.max=f.max;}
const save=el('button','Save'),clear=el('button','Clear');for(const n of [input,save,clear])n.disabled=busy||r.status!=='draft';save.onclick=()=>{let v=input.value;if(f.type==='integer')v=v===''?null:Number(v);else if(f.type==='boolean')v=v===''?null:v==='true';else if(f.type==='choice'&&v==='')v=null;write(f.id,v);};clear.onclick=()=>write(f.id,null);row.append(input,save,clear);root.append(row);}
root.append(el('h3','Archived answers'));for(const a of r.archive)root.append(el('p',`${a.fieldId}: ${JSON.stringify(a.value)} (${a.reason}, v${a.fromVersion} → v${a.toVersion})`));}
async function write(fieldId,value){if(busy||!current)return;const token=generation,id=selected,rev=current.revision;busy=true;render();message('Saving…');try{const r=await api.save(id,{fieldId,value,expectedRevision:rev});if(token!==generation)return;current=r;message('Saved');await loadList();}catch(e){if(token!==generation)return;try{const r=await api.detail(id);if(token!==generation)return;current=r;}catch{}message(e.message);}finally{if(token===generation){busy=false;render();}}}
loadList().catch(e=>message(e.message));
