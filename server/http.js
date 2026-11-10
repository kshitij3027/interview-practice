import http from 'node:http';
import { readFileSync } from 'node:fs';
import { DomainError, createStore, listOrganizations, listCustomers, listFlags, getFlag, editNote } from './domain.js';

const staticFiles = new Map([
  ['/', ['../public/index.html','text/html; charset=utf-8']],
  ['/app.js', ['../public/app.js','text/javascript; charset=utf-8']],
  ['/api.js', ['../public/api.js','text/javascript; charset=utf-8']],
  ['/styles.css', ['../public/styles.css','text/css; charset=utf-8']]
]);
function send(res, status, data) {
  res.writeHead(status, {'content-type':'application/json; charset=utf-8', 'cache-control':'no-store'});
  res.end(JSON.stringify(data));
}
async function jsonBody(req) {
  let text = '';
  for await (const chunk of req) {
    text += chunk.toString('utf8');
    if (Buffer.byteLength(text, 'utf8') > 32 * 1024) throw new DomainError(413, 'TOO_LARGE', 'Request body too large');
  }
  try { return JSON.parse(text); } catch { throw new DomainError(400, 'INVALID_JSON', 'Invalid JSON body'); }
}
export function createServer(store = createStore()) {
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && staticFiles.has(url.pathname)) {
        const [path, type] = staticFiles.get(url.pathname);
        res.writeHead(200, {'content-type':type});
        res.end(readFileSync(new URL(path, import.meta.url)));
        return;
      }
      const orgId = url.searchParams.get('org');
      if (req.method === 'GET' && url.pathname === '/api/organizations') return send(res, 200, listOrganizations(store));
      if (req.method === 'GET' && url.pathname === '/api/customers') return send(res, 200, listCustomers(store, orgId));
      if (req.method === 'GET' && url.pathname === '/api/flags') {
        const rawLimit = url.searchParams.get('limit');
        const limit = rawLimit === null ? 50 : Number(rawLimit);
        return send(res, 200, listFlags(store, {orgId, search:url.searchParams.get('search') ?? '', status:url.searchParams.get('status') ?? 'all', limit}));
      }
      const match = /^\/api\/flags\/([^/]+)(\/note)?$/.exec(url.pathname);
      if (match) {
        const flagId = decodeURIComponent(match[1]);
        if (req.method === 'GET' && !match[2]) return send(res, 200, getFlag(store, orgId, flagId));
        if (req.method === 'PATCH' && match[2]) return send(res, 200, editNote(store, orgId, flagId, await jsonBody(req)));
      }
      send(res, 404, {error:{code:'NOT_FOUND',message:'Not found'}});
    } catch (error) {
      if (error instanceof DomainError) return send(res, error.status, {error:{code:error.code,message:error.message}});
      send(res, 500, {error:{code:'INTERNAL',message:'Unexpected error'}});
    }
  });
}
