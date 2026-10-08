import { loadFixtures } from './data.js';
const copy = value => structuredClone(value);
export class HttpError extends Error {
  constructor(status, code, message) { super(message); this.status=status; this.code=code; }
}
export function createStore(fixtures = loadFixtures()) {
  const shipments = new Map(fixtures.shipments.map(s=>[s.id,{...copy(s),temperatureHold:false}]));
  const counts = new Map();
  for (const r of fixtures.readings) counts.set(r.shipmentId,(counts.get(r.shipmentId)||0)+1);
  let datasetRevision = 1;
  function lookup(id) {
    const s=shipments.get(id);
    if(!s) throw new HttpError(404,'not_found','Shipment not found');
    return s;
  }
  function list({site='',state='',search=''}={}) {
    if(site && !['west','east','central'].includes(site)) throw new HttpError(400,'bad_filter','Unknown site');
    if(state && !['active','closed'].includes(state)) throw new HttpError(400,'bad_filter','Unknown state');
    const q=String(search).trim().toLowerCase();
    const items=[...shipments.values()].filter(s=>(!site||s.site===site)&&(!state||s.state===state)&&(!q||(s.id+' '+s.customer+' '+s.label).toLowerCase().includes(q)))
      .sort((a,b)=>a.site.localeCompare(b.site)||a.customer.localeCompare(b.customer)||a.id.localeCompare(b.id))
      .map(({id,site,state,label,customer,route,revision,temperatureHold})=>({id,site,state,label,customer,route,revision,temperatureHold}));
    return {items,datasetRevision};
  }
  function detail(id) { return {shipment:copy(lookup(id)),readingCount:counts.get(id)||0,datasetRevision}; }
  function setNote(id,{expectedRevision,note}) {
    const s=lookup(id);
    if(!Number.isInteger(expectedRevision)||typeof note!=='string'||note.length>500) throw new HttpError(400,'invalid_note','Invalid note or revision');
    if(expectedRevision!==s.revision) throw new HttpError(409,'stale_revision','Shipment has changed');
    const value=note.trim();
    if(value===s.operatorNote.trim()) return {changed:false,...detail(id)};
    s.operatorNote=value;s.revision++;datasetRevision++;
    return {changed:true,...detail(id)};
  }
  return {list,detail,setNote};
}
