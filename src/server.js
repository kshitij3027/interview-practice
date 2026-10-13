import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {extname, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createStore} from './store.js';

const root = resolve(fileURLToPath(new URL('../web/', import.meta.url)));
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};

function reply(res, status, data) {
  res.writeHead(status, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
  res.end(JSON.stringify(data));
}
function parseLimit(text) {
  if (text === null) return 10;
  if (!/^\d+$/.test(text)) throw Object.assign(new Error('limit must be 1..50'), {status:400, code:'bad_limit'});
  const n = Number(text);
  if (!Number.isSafeInteger(n) || n < 1 || n > 50) throw Object.assign(new Error('limit must be 1..50'), {status:400, code:'bad_limit'});
  return n;
}
async function readBody(req) {
  let contents = '';
  for await (const chunk of req) {
    contents += chunk;
    if (contents.length > 32_768) throw Object.assign(new Error('Request too large'), {status:413, code:'too_large'});
  }
  try { return JSON.parse(contents); }
  catch { throw Object.assign(new Error('Invalid JSON'), {status:400, code:'bad_json'}); }
}
async function staticFile(req, res, pathname) {
  const filename = pathname === '/' ? 'index.html' : decodeURIComponent(pathname.slice(1));
  const full = resolve(root, filename);
  if (!(full === root || full.startsWith(root + sep)) || !mime[extname(full)]) return reply(res, 404, {error:'not_found'});
  try {
    const data = await readFile(full);
    res.writeHead(200, {'content-type':mime[extname(full)], 'cache-control':'no-store'});
    res.end(data);
  } catch { reply(res, 404, {error:'not_found'}); }
}
export function createApp(store = createStore()) {
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      const path = url.pathname;
      if (path === '/api/health' && req.method === 'GET') return reply(res, 200, {ok:true});
      if (path === '/api/tenants' && req.method === 'GET') return reply(res, 200, store.tenants());
      if (path === '/api/articles' && req.method === 'GET') return reply(res, 200, store.search({
        tenantId:url.searchParams.get('tenantId'), query:url.searchParams.get('q') ?? '',
        category:url.searchParams.get('category') ?? 'all', limit:parseLimit(url.searchParams.get('limit'))
      }));
      const match = /^\/api\/articles\/([a-z0-9-]+)(?:\/note)?$/.exec(path);
      if (match && req.method === 'GET' && !path.endsWith('/note'))
        return reply(res, 200, store.article(url.searchParams.get('tenantId'), match[1]));
      if (match && req.method === 'PATCH' && path.endsWith('/note')) {
        const body = await readBody(req);
        return reply(res, 200, store.updateNote({tenantId:body.tenantId, id:match[1],
          expectedRevision:body.expectedRevision, note:body.note}));
      }
      if (path.startsWith('/api/')) return reply(res, 404, {error:'not_found'});
      if (req.method !== 'GET') return reply(res, 405, {error:'method_not_allowed'});
      return await staticFile(req, res, path);
    } catch (error) {
      reply(res, error.status ?? 500, {error:error.code ?? 'internal_error', message:error.status ? error.message : 'Internal error'});
    }
  });
}
if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  const port = Number(process.env.PORT ?? 8080);
  createApp().listen(port, '0.0.0.0', () => console.log(`FindFix running at http://localhost:${port}`));
}
