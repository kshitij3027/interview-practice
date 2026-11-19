import http from 'node:http';
import {readFileSync} from 'node:fs';
import {extname,join,resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {organizations,details,list,editNote,DomainError} from './domain.js';
const root=resolve(fileURLToPath(new URL('../public/',import.meta.url)));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
const send=(res,status,payload)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(payload));};
async function readJson(req){let body='';for await(const c of req){body+=c;if(body.length>32768)throw new DomainError(413,'BODY_TOO_LARGE','Body exceeds 32 KiB');}try{return JSON.parse(body);}catch{throw new DomainError(400,'BAD_JSON','Malformed JSON');}}
export function createServer(db){return http.createServer(async(req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname.startsWith('/api/')){
      if(req.method==='GET'&&url.pathname==='/api/organizations')return send(res,200,{items:organizations(db)});
      if(req.method==='GET'&&url.pathname==='/api/sessions')return send(res,200,list(db,{orgId:url.searchParams.get('orgId'),q:url.searchParams.get('q')||'',phase:url.searchParams.get('phase')||'all',offset:Number(url.searchParams.get('offset')||0),limit:Number(url.searchParams.get('limit')||20)}));
      const m=url.pathname.match(/^\/api\/sessions\/([a-zA-Z0-9-]+)(?:\/note)?$/);
      if(m){const orgId=url.searchParams.get('orgId');if(req.method==='GET'&&!url.pathname.endsWith('/note'))return send(res,200,details(db,m[1],orgId));if(req.method==='PUT'&&url.pathname.endsWith('/note'))return send(res,200,editNote(db,m[1],orgId,await readJson(req)));}
      return send(res,404,{error:{code:'NOT_FOUND',message:'Route not found'}});
    }
    if(req.method!=='GET'&&req.method!=='HEAD')return send(res,405,{error:{code:'METHOD',message:'Unsupported method'}});
    const p=url.pathname==='/'?'/index.html':url.pathname;
    const full=resolve(join(root,p));
    if(!full.startsWith(root+sep))return send(res,404,{error:{code:'NOT_FOUND',message:'Missing file'}});
    try{const b=readFileSync(full);res.writeHead(200,{'Content-Type':mime[extname(full)]||'application/octet-stream'});res.end(b);}catch{return send(res,404,{error:{code:'NOT_FOUND',message:'Missing file'}});}
  }catch(e){send(res,e instanceof DomainError?e.status:500,{error:{code:e.code||'INTERNAL',message:e instanceof DomainError?e.message:'Internal error',...(e.current?{current:e.current}:{})}});}
});}
