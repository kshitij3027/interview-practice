import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { makeStore } from './store.mjs';
import { createRouter } from './routes.mjs';
import { ApiError } from './errors.mjs';

const root=resolve(fileURLToPath(new URL('../web/', import.meta.url)));
const contentTypes={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
export function startServer({port=8080,store=makeStore()}={}) {
  const route=createRouter(store);
  const server=createServer(async(req,res)=>{
    try {
      if ((req.url||'').startsWith('/api/')) {
        const incoming={method:req.method,url:req.url,json:async()=>{
          const chunks=[]; for await (const chunk of req) chunks.push(chunk);
          const raw=Buffer.concat(chunks).toString('utf8');
          if (raw.length>50000) throw new ApiError(413,'too_large','Request exceeds 50 KB');
          try{return JSON.parse(raw)}catch{throw new ApiError(400,'bad_json','Expected JSON body')}
        }};
        const out=await route(incoming);
        res.writeHead(200,{'content-type':'application/json; charset=utf-8'}); res.end(JSON.stringify(out));return;
      }
      if (req.method !== 'GET') throw new ApiError(405,'method_not_allowed','Method not allowed');
      const name=new URL(req.url,'http://localhost').pathname;
      const relative=name==='/'?'index.html':name.replace(/^\//,'');
      const file=resolve(join(root,relative));
      if(!file.startsWith(root+'/') && file!==root) throw new ApiError(404,'not_found','Not found');
      const body=readFileSync(file);
      res.writeHead(200,{'content-type':contentTypes[extname(file)]||'application/octet-stream'});res.end(body);
    } catch(e) {
      const status=e instanceof ApiError ? e.status : (e.code === 'ENOENT'?404:500);
      res.writeHead(status,{'content-type':'application/json; charset=utf-8'});
      res.end(JSON.stringify({error:e instanceof ApiError?e.code:'server_error',message:status===500?'Unexpected server error':e.message,details:e.details||{}}));
    }
  });
  server.listen(port);return server;
}
if (process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const port=Number(process.env.PORT || 8080);
  startServer({port}); console.log('CaseFuse at http://localhost:'+port);
}
