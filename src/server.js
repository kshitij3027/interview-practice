import http from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createStore, DomainError } from './domain.js';

const assets = new Map([
  ['/', ['../web/index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['../web/app.js', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['../web/styles.css', 'text/css; charset=utf-8']],
]);

function respond(res, status, value, type = 'application/json; charset=utf-8') {
  res.writeHead(status, { 'content-type': type, 'cache-control': 'no-store' });
  res.end(type.startsWith('application/json') ? JSON.stringify(value) : value);
}

async function readJSON(req) {
  let body = '';
  for await (const chunk of req) {
    body += chunk.toString('utf8');
    if (body.length > 65536) throw new DomainError(413, 'body_too_large', 'Payload too large');
  }
  try { return JSON.parse(body); }
  catch { throw new DomainError(400, 'invalid_json', 'Expected JSON request body'); }
}

export function createServer(store = createStore()) {
  return http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && url.pathname === '/health') return respond(res, 200, { ok: true });
      if (req.method === 'GET' && url.pathname === '/api/employees') return respond(res, 200, store.employees());
      if (req.method === 'GET' && url.pathname === '/api/shifts') {
        return respond(res, 200, store.listShifts(Object.fromEntries(url.searchParams)));
      }
      const note = /^\/api\/shifts\/([^/]+)\/note$/.exec(url.pathname);
      const detail = /^\/api\/shifts\/([^/]+)$/.exec(url.pathname);
      if (req.method === 'GET' && detail) return respond(res, 200, store.getShift(decodeURIComponent(detail[1])));
      if (req.method === 'PATCH' && note) {
        return respond(res, 200, await store.saveNote(decodeURIComponent(note[1]), await readJSON(req)));
      }
      if (req.method === 'GET' && assets.has(url.pathname)) {
        const [file, type] = assets.get(url.pathname);
        return respond(res, 200, readFileSync(fileURLToPath(new URL(file, import.meta.url)), 'utf8'), type);
      }
      return respond(res, 404, { error: { code: 'not_found', message: 'Route not found' } });
    } catch (error) {
      if (error instanceof DomainError) {
        return respond(res, error.status, { error: { code: error.code, message: error.message, ...error.details } });
      }
      console.error(error);
      return respond(res, 500, { error: { code: 'internal_error', message: 'Unexpected server error' } });
    }
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const port = Number(process.env.PORT || 8080);
  createServer().listen(port, () => console.log(`ShiftPay available at http://localhost:${port}`));
}
