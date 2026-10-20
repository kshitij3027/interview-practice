import { URL } from 'node:url';
import { ApiError, bad } from './errors.mjs';

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
function delay(value) {
  const n = value === undefined ? 0 : Number(value);
  if (!Number.isSafeInteger(n) || n < 0 || n > 1200 || (value !== undefined && String(n) !== String(value))) throw bad('invalid_delay','delayMs must be an integer 0–1200');
  return n;
}
export function createRouter(store) {
  return async function route(request) {
    const url = new URL(request.url, 'http://localhost');
    const pathname = decodeURIComponent(url.pathname);
    if (request.method === 'GET' && pathname === '/api/health') return {ok:true,service:'casefuse'};
    if (request.method === 'GET' && pathname === '/api/cases') {
      const ms=delay(url.searchParams.get('delayMs') ?? undefined);
      const filters = Object.fromEntries(['tenant','status','q'].map(k => [k,url.searchParams.get(k) ?? (k==='q'?'':'all')]));
      if (!['all','north','south'].includes(filters.tenant)) throw bad('invalid_tenant','Unsupported tenant');
      if (!['all','open','pending','resolved','merged'].includes(filters.status)) throw bad('invalid_status','Unsupported status');
      await wait(ms); return store.list(filters);
    }
    const hit = pathname.match(/^\/api\/cases\/([^/]+)(?:\/(note))?$/);
    if (hit && request.method === 'GET' && !hit[2]) {
      await wait(delay(url.searchParams.get('delayMs') ?? undefined)); return store.get(hit[1]);
    }
    if (hit && request.method === 'PATCH' && hit[2] === 'note') {
      const body=await request.json();
      await wait(delay(body.delayMs)); return store.updateNote(hit[1],body);
    }
    throw new ApiError(404,'route_not_found','No such endpoint');
  };
}
