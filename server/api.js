import { HttpError } from './store.js';
export function send(res,status,data){
  res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
  res.end(JSON.stringify(data));
}
async function bodyJson(req){
  let raw='';
  for await(const chunk of req){raw+=chunk;if(raw.length>16384)throw new HttpError(413,'too_large','Body too large');}
  try{const data=JSON.parse(raw);if(!data||typeof data!=='object'||Array.isArray(data))throw Error();return data;}
  catch{throw new HttpError(400,'invalid_json','Expected a JSON object');}
}
export async function handleApi(store,req,res,url){
  const path=url.pathname.split('/').filter(Boolean);
  if(path[0]!=='api')return false;
  if(req.method==='GET'&&url.pathname==='/api/health')return send(res,200,{ok:true}),true;
  if(req.method==='GET'&&url.pathname==='/api/shipments'){
    send(res,200,store.list({site:url.searchParams.get('site')||'',state:url.searchParams.get('state')||'',search:url.searchParams.get('search')||''}));
    return true;
  }
  if(path.length===3&&path[1]==='shipments'&&req.method==='GET'){
    send(res,200,store.detail(path[2]));return true;
  }
  if(path.length===4&&path[1]==='shipments'&&path[3]==='note'&&req.method==='PATCH'){
    send(res,200,store.setNote(path[2],await bodyJson(req)));return true;
  }
  send(res,404,{error:'not_found',message:'Unknown API route'});return true;
}
