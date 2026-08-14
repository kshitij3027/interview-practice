import { readJson, sendJson } from './http.js';

export function createHandler(service) {
  return async function handler(req, res) {
    if (req.method === 'OPTIONS') return sendJson(res, 204, {});
    const url = new URL(req.url, 'http://localhost');

    if (req.method === 'GET' && url.pathname === '/api/overview') return sendJson(res, 200, service.overview());
    if (req.method === 'GET' && url.pathname === '/api/users') return sendJson(res, 200, service.users());

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
