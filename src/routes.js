import { readJson, sendJson } from './http.js';

export const MAX_DELAY_MS = 5000;

// A local test knob, so stale-response behaviour can be exercised without external
// infrastructure. Malformed input fails safe to "no delay" rather than erroring: a broken
// debug parameter must never break the report. Only a valid oversized number is clamped to
// the ceiling — non-finite input is malformed, not "very large".
export function parseDelayMs(raw) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(Math.trunc(value), MAX_DELAY_MS);
}

const sleep = ms => (ms > 0 ? new Promise(resolve => setTimeout(resolve, ms)) : Promise.resolve());

export function createHandler(service) {
  return async function handler(req, res) {
    if (req.method === 'OPTIONS') return sendJson(res, 204, {});
    const url = new URL(req.url, 'http://localhost');

    if (req.method === 'GET' && url.pathname === '/api/overview') return sendJson(res, 200, service.overview());
    if (req.method === 'GET' && url.pathname === '/api/users') return sendJson(res, 200, service.users());

    if (req.method === 'GET' && url.pathname === '/api/funnel') {
      const result = service.funnel({ segment: url.searchParams.get('segment') ?? 'all' });
      if (!result.ok) return sendJson(res, 400, { error: result.code });
      const { ok, ...body } = result;
      // Compute first, then sleep. Sleeping before computing would yield a slow but *fresh*
      // response, which is useless for exercising stale-response handling: the point of the
      // delay is that the response carries the revision from before an exclusion landed.
      await sleep(parseDelayMs(url.searchParams.get('delay_ms')));
      return sendJson(res, 200, body);
    }

    const match = url.pathname.match(/^\/api\/users\/([^/]+)\/exclusion$/);
    if (req.method === 'PATCH' && match) {
      try {
        const body = await readJson(req);
        const result = service.setExclusion(decodeURIComponent(match[1]), Boolean(body.excluded), body.reason);
        if (!result.ok) return sendJson(res, result.code === 'not_found' ? 404 : 400, { error: result.code });
        return sendJson(res, 200, result);
      } catch {
        return sendJson(res, 400, { error: 'invalid_json' });
      }
    }
    return sendJson(res, 404, { error: 'not_found' });
  };
}
