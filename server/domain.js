export class DomainError extends Error {
  constructor(status, code, message, current=null) { super(message); Object.assign(this,{status,code,current}); }
}
const fail=(status,code,message,current)=>{throw new DomainError(status,code,message,current);};
export function organizations(db) {return structuredClone(db.organizations);}
export function session(db,id,orgId) {
  if (!db.organizations.some(o=>o.id===orgId)) fail(404,'NOT_FOUND','Organization not found');
  const item=db.sessions.find(s=>s.id===id&&s.orgId===orgId);
  if (!item) fail(404,'NOT_FOUND','Session not found');
  return item;
}
export function details(db,id,orgId) {return structuredClone(session(db,id,orgId));}
export function list(db,{orgId,q='',phase='all',offset=0,limit=20}) {
  if (!db.organizations.some(o=>o.id===orgId)) fail(404,'NOT_FOUND','Organization not found');
  if (!['all','open','closed'].includes(phase)) fail(400,'INVALID_FILTER','Invalid phase');
  if (!Number.isInteger(offset)||offset<0||offset>100000 || !Number.isInteger(limit)||limit<1||limit>100) fail(400,'INVALID_PAGE','Invalid pagination');
  const term=q.trim().toLowerCase();
  const items=db.sessions.filter(s=>s.orgId===orgId&&(phase==='all'||s.phase===phase)&&(s.title.toLowerCase().includes(term)||s.id.toLowerCase().includes(term))).sort((a,b)=>a.id.localeCompare(b.id));
  return {total:items.length,offset,limit,items:items.slice(offset,offset+limit).map(s=>({id:s.id,title:s.title,orgId:s.orgId,phase:s.phase,capacity:s.capacity,confirmed:s.people.filter(p=>p.status==='confirmed').length,waiting:s.people.filter(p=>p.status==='waiting').length,revision:s.revision}))};
}
export function editNote(db,id,orgId,body) {
  const item=session(db,id,orgId);
  if (!body||typeof body!=='object'||Array.isArray(body)||typeof body.note!=='string'||body.note.length>2000||!Number.isSafeInteger(body.expectedRevision)||body.expectedRevision<0) fail(400,'INVALID_NOTE','Invalid note input');
  if (body.expectedRevision!==item.revision) fail(409,'STALE_REVISION','Session changed',structuredClone(item));
  const next=body.note.trim();
  if (next!==item.note) {item.note=next;item.revision++;}
  return structuredClone(item);
}
