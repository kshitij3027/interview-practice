import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createStore } from './store.mjs';
import { delayValue, fail } from './validation.mjs';

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../web');
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function readBody(req) {
  let data = '';
  for await (const part of req) {
    data += part;
    if (data.length > 30000) fail(413, 'too_large', 'Request too large');
  }
  try { return data ? JSON.parse(data) : {}; }
  catch { fail(400, 'bad_json', 'Malformed JSON'); }
}

function send(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}

export function createServer(store = createStore()) {
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? '/', 'http://localhost');
      const parts = url.pathname.split('/').filter(Boolean);
      if (parts[0] === 'api') {
        const delay = delayValue(url.searchParams.get('delayMs'));
        if (delay) await sleep(delay);
        if (req.method === 'GET' && url.pathname === '/api/health') return send(res, 200, { ok: true });
        if (req.method === 'GET' && url.pathname === '/api/campaigns') return send(res, 200, store.listCampaigns());
        if (req.method === 'GET' && parts[1] === 'campaigns' && parts.length === 3) return send(res, 200, store.getCampaign(parts[2]));
        if (req.method === 'GET' && url.pathname === '/api/contacts') return send(res, 200, store.listContacts(Object.fromEntries(url.searchParams)));
        if (parts[1] === 'contacts' && parts.length === 3 && req.method === 'GET') return send(res, 200, store.getContact(parts[2]));
        if (parts[1] === 'contacts' && parts[3] === 'note' && parts.length === 4 && req.method === 'PUT') {
          return send(res, 200, store.updateContactNote(parts[2], await readBody(req)));
        }
        return send(res, 404, { error: { code: 'not_found', message: 'Unknown API route' } });
      }
      if (req.method !== 'GET') return send(res, 405, { error: { code: 'method_not_allowed', message: 'GET required' } });
      const filename = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
      if (!['index.html', 'app.js', 'styles.css'].includes(filename)) return send(res, 404, { error: { code: 'not_found', message: 'Not found' } });
      const body = await fs.readFile(path.join(webRoot, filename));
      res.writeHead(200, { 'Content-Type': mime[path.extname(filename)], 'Cache-Control': 'no-store' });
      res.end(body);
    } catch (error) {
      if (res.headersSent) return res.end();
      send(res, error.status ?? 500, { error: { code: error.code ?? 'internal_error', message: error.status ? error.message : 'Internal error' } });
    }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT ?? 8080);
  createServer().listen(port, () => console.log(`WaveSend listening at http://localhost:${port}`));
}
