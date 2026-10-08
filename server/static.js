import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..','client');
const names=new Set(['index.html','app.js','api-client.js','list.js','detail.js','detail_view.js','style.css']);
export function serveStatic(req,res,url){const name=url.pathname==='/'?'index.html':url.pathname.slice(1);if(req.method!=='GET'||!names.has(name))return false;res.writeHead(200,{'content-type':'text/'+(name.endsWith('.css')?'css':name.endsWith('.html')?'html':'javascript')+'; charset=utf-8'});res.end(readFileSync(join(root,name)));return true;}
