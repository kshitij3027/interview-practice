import { readFile } from 'node:fs/promises';
import { extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ApiError } from './store.js';

const publicDir = fileURLToPath(new URL('../public/', import.meta.url));
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

export function json(res, status, payload) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(payload));
}

export async function requestJson(req) {
  let data = '';
  for await (const chunk of req) {
    data += chunk;
    if (data.length > 65536) throw new ApiError(413, 'request too large');
  }
  try { return JSON.parse(data); } catch { throw new ApiError(400, 'invalid JSON'); }
}

export async function staticFile(url, res) {
  const name = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
  if (!['index.html', 'app.js', 'styles.css'].includes(name)) throw new ApiError(404, 'not found');
  const bytes = await readFile(resolve(publicDir, name));
  res.writeHead(200, { 'content-type': mime[extname(name)], 'cache-control': 'no-store' });
  res.end(bytes);
}
