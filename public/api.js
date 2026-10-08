async function req(url,options){const res=await fetch(url,options);const data=await res.json();if(!res.ok){const e=Error(data.error?.message||'Request failed');e.code=data.error?.code;e.current=data.error?.current;throw e;}return data;}
export function listBins(filters){const p=new URLSearchParams();for(const [k,v] of Object.entries(filters))if(v)p.set(k,v);return req('/api/bins?'+p);}
export function getBin(id){return req('/api/bins/'+encodeURIComponent(id));}
export function saveNote(id,revision,note){return req('/api/bins/'+encodeURIComponent(id)+'/note',{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({note,expectedRevision:revision})});}
