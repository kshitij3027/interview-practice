import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {BinStore,DomainError} from './lib/store.js';
const DIR=fileURLToPath(new URL('./public/',import.meta.url));
const respond=(res,status,data)=>{res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store'});res.end(JSON.stringify(data));};
async function parse(req){let s='';for await(const part of req){s+=part;if(s.length>20000)throw new DomainError(413,'too_large','Body too large');}try{const data=JSON.parse(s);if(!data||Array.isArray(data)||typeof data!=='object')throw Error();return data;}catch{throw new DomainError(400,'invalid_json','JSON object expected');}}
export function createServer(store=new BinStore()){return http.createServer(async(req,res)=>{try{
  const url=new URL(req.url,'http://localhost');const note=/^\/api\/bins\/([^/]+)\/note$/.exec(url.pathname);const detail=/^\/api\/bins\/([^/]+)$/.exec(url.pathname);
  if(req.method==='GET'&&url.pathname==='/api/health')return respond(res,200,{ok:true});
  if(req.method==='GET'&&url.pathname==='/api/bins')return respond(res,200,store.list({zone:url.searchParams.get('zone')||'',status:url.searchParams.get('status')||'',q:url.searchParams.get('q')||''}));
  if(req.method==='GET'&&detail)return respond(res,200,store.detail(decodeURIComponent(detail[1])));
  if(req.method==='PATCH'&&note){const p=await parse(req);return respond(res,200,store.setNote(decodeURIComponent(note[1]),p.note,p.expectedRevision));}
  if(url.pathname.startsWith('/api/'))throw new DomainError(404,'not_found','Unknown route');
  if(req.method!=='GET')throw new DomainError(405,'method_not_allowed','GET only');
  const file=url.pathname==='/'?'index.html':url.pathname.slice(1);if(!['index.html','app.js','api.js','styles.css'].includes(file))throw new DomainError(404,'not_found','Resource not found');
  const bytes=await readFile(path.join(DIR,file));const ext=path.extname(file);res.writeHead(200,{'content-type':ext==='.js'?'text/javascript; charset=utf-8':ext==='.css'?'text/css; charset=utf-8':'text/html; charset=utf-8'});res.end(bytes);
}catch(e){if(e instanceof DomainError)return respond(res,e.status,{error:{code:e.code,message:e.message,current:e.current}});console.error(e);respond(res,500,{error:{code:'internal_error',message:'Internal error'}});}});}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){const port=Number(process.env.PORT||8080);createServer().listen(port,()=>console.log('StockAudit at http://localhost:'+port));}
