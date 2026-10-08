import { createServer as httpServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { OrderStore, ApiError } from './store.js';
import { json, requestJson, staticFile } from './http.js';

export function createApp(store = new OrderStore()) {
  return httpServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && url.pathname === '/api/health') return json(res, 200, { ok: true });
      if (req.method === 'GET' && url.pathname === '/api/orders') {
        return json(res, 200, store.list({ search: url.searchParams.get('search') ?? '', status: url.searchParams.get('status') ?? '' }));
      }
      const match = url.pathname.match(/^\/api\/orders\/(ORD-[A-Za-z0-9-]+)(?:\/note)?$/);
      if (match && req.method === 'GET' && !url.pathname.endsWith('/note')) return json(res, 200, store.detail(match[1]));
      if (match && req.method === 'PATCH' && url.pathname.endsWith('/note')) {
        return json(res, 200, store.updateNote(match[1], await requestJson(req)));
      }
      if (req.method === 'GET') return await staticFile(url, res);
      throw new ApiError(404, 'route not found');
    } catch (error) {
      if (error instanceof ApiError) return json(res, error.status, { error: error.message, ...error.details });
      console.error(error);
      return json(res, 500, { error: 'internal server error' });
    }
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === fileURLToPath(new URL(`file://${process.argv[1]}`))) {
  const port = Number(process.env.PORT || 8080);
  createApp().listen(port, () => console.log(`ReturnCredit at http://localhost:${port}`));
}
