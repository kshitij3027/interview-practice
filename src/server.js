import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadFixtures } from './fixtures.js';
import { SuiteStore } from './store.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const publicDir = path.join(root, 'public');
const store = new SuiteStore(loadFixtures());

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'content-length': Buffer.byteLength(payload) });
  res.end(payload);
}

async function readJson(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString('utf8');
  if (!text) return {};
  try { return JSON.parse(text); }
  catch { throw new Error('request body must be valid JSON'); }
}

function serveStatic(req, res, pathname) {
  const wanted = pathname === '/' ? '/index.html' : pathname;
  const normalized = path.normalize(wanted).replace(/^([.][.][/\\])+/, '');
  const filePath = path.join(publicDir, normalized);
  if (!filePath.startsWith(publicDir) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return false;
  const ext = path.extname(filePath);
  const type = ext === '.html' ? 'text/html; charset=utf-8' : ext === '.js' ? 'text/javascript; charset=utf-8' : ext === '.css' ? 'text/css; charset=utf-8' : 'application/octet-stream';
  res.writeHead(200, { 'content-type': type });
  fs.createReadStream(filePath).pipe(res);
  return true;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const pathname = url.pathname;

  if (req.method === 'GET' && pathname === '/api/health') {
    return json(res, 200, { ok: true, datasetRevision: store.datasetRevision });
  }

  if (req.method === 'GET' && pathname === '/api/suites') {
    const suites = store.listSuites({ owner: url.searchParams.get('owner') || '', status: url.searchParams.get('status') || '' });
    return json(res, 200, { suites, datasetRevision: store.datasetRevision });
  }

  const match = pathname.match(/^\/api\/suites\/([^/]+)$/);
  if (req.method === 'GET' && match) {
    const suite = store.getSuite(decodeURIComponent(match[1]));
    return suite ? json(res, 200, { suite }) : json(res, 404, { error: 'suite_not_found' });
  }

  const noteMatch = pathname.match(/^\/api\/suites\/([^/]+)\/note$/);
  if (req.method === 'POST' && noteMatch) {
    try {
      const result = store.updateNote(decodeURIComponent(noteMatch[1]), await readJson(req));
      return json(res, result.status, result.body);
    } catch (error) {
      return json(res, 400, { error: error.message });
    }
  }

  if (req.method === 'GET' && serveStatic(req, res, pathname)) return;
  json(res, 404, { error: 'not_found' });
});

const port = Number(process.env.PORT || 8080);
if (process.env.NODE_ENV !== 'test') {
  server.listen(port, () => console.log('EvalBoard listening on http://localhost:' + port));
}

export { server, store };
