import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { DomainError } from './store.js';

const publicFiles = new Map([
  ['/', ['../public/index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['../public/app.js', 'text/javascript; charset=utf-8']],
  ['/api.js', ['../public/api.js', 'text/javascript; charset=utf-8']],
  ['/style.css', ['../public/style.css', 'text/css; charset=utf-8']]
]);

function send(res, status, data) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(data));
}

async function readJson(req) {
  let text = '';
  for await (const chunk of req) {
    text += chunk;
    if (text.length > 16_384) throw new DomainError(413, 'BODY_TOO_LARGE', 'Request body is too large.');
  }
  try {
    const value = JSON.parse(text);
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('not object');
    return value;
  } catch {
    throw new DomainError(400, 'INVALID_JSON', 'Expected a JSON object.');
  }
}

export function handler(store) {
  return async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      const path = url.pathname;
      if (req.method === 'GET' && path === '/api/health') return send(res, 200, { ok: true });
      if (req.method === 'GET' && path === '/api/studios') return send(res, 200, store.listStudios());
      if (req.method === 'GET' && path === '/api/assets') {
        const rawLimit = url.searchParams.get('limit');
        const limit = rawLimit === null ? 50 : Number(rawLimit);
        return send(res, 200, store.listAssets({ studio: url.searchParams.get('studio'),
          status: url.searchParams.get('status') || '', q: url.searchParams.get('q') || '', limit }));
      }
      const note = /^\/api\/assets\/([^/]+)\/note$/.exec(path);
      if (req.method === 'PATCH' && note) {
        const body = await readJson(req);
        return send(res, 200, store.editNote(decodeURIComponent(note[1]), url.searchParams.get('studio'), body.note, body.expectedRevision));
      }
      const detail = /^\/api\/assets\/([^/]+)$/.exec(path);
      if (req.method === 'GET' && detail) {
        return send(res, 200, store.getAsset(decodeURIComponent(detail[1]), url.searchParams.get('studio')));
      }
      if (req.method === 'GET' && publicFiles.has(path)) {
        const [relative, type] = publicFiles.get(path);
        const data = await readFile(fileURLToPath(new URL(relative, import.meta.url)));
        res.writeHead(200, { 'content-type': type, 'cache-control': 'no-store' });
        res.end(data);
        return;
      }
      return send(res, 404, { error: { code: 'NOT_FOUND', message: 'Route not found.' } });
    } catch (error) {
      if (error instanceof DomainError) return send(res, error.status, { error: { code: error.code, message: error.message } });
      console.error(error);
      return send(res, 500, { error: { code: 'INTERNAL', message: 'Unexpected server error.' } });
    }
  };
}
