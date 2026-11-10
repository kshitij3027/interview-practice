import { createServer } from './http.js';
const port = Number(process.env.PORT ?? 8080);
createServer().listen(port, '127.0.0.1', () => console.log(`FlagHarbor: http://127.0.0.1:${port}`));
