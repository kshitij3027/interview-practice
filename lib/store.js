import {loadBins,noteValue} from './catalog.js';
export class DomainError extends Error { constructor(status,code,message,current=null){super(message);Object.assign(this,{status,code,current});} }
export class BinStore {
  constructor(bins=loadBins()){this.bins=new Map(structuredClone(bins).map(x=>[x.id,x]));this.datasetRevision=1;}
  detail(id){const bin=this.bins.get(id);if(!bin)throw new DomainError(404,'not_found','Unknown bin');return {datasetRevision:this.datasetRevision,bin:structuredClone(bin)};}
  list({zone='',status='',q=''}={}){
    const query=q.trim().toLowerCase();const items=[...this.bins.values()].filter(b=>(!zone||b.zone===zone)&&(!status||b.status===status)&&(!query||[b.id,b.sku,b.label].join(' ').toLowerCase().includes(query))).sort((a,b)=>a.zone.localeCompare(b.zone)||a.id.localeCompare(b.id));
    return {datasetRevision:this.datasetRevision,total:items.length,items:items.map(b=>({id:b.id,zone:b.zone,sku:b.sku,status:b.status,onHand:b.onHand,revision:b.revision}))};
  }
  setNote(id,note,expectedRevision){const b=this.bins.get(id);if(!b)throw new DomainError(404,'not_found','Unknown bin');if(!Number.isSafeInteger(expectedRevision)||expectedRevision<1)throw new DomainError(400,'invalid_revision','expectedRevision must be positive integer');let value;try{value=noteValue(note);}catch(e){throw new DomainError(400,'invalid_note',e.message);}
    if(b.revision!==expectedRevision)throw new DomainError(409,'stale_bin','Bin changed; refresh first',this.detail(id));const changed=value!==b.note;if(changed){b.note=value;b.revision++;this.datasetRevision++;}return {...this.detail(id),changed};}
}
