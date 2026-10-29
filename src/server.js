import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { handler } from './http.js';
import { createStore } from './store.js';

const fixturePath = fileURLToPath(new URL('../fixtures/catalog.json', import.meta.url));

export function createApp(seed = JSON.parse(readFileSync(fixturePath, 'utf8'))) {
  const store = createStore(seed);
  return { server: createServer(handler(store)), store };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const port = Number(process.env.PORT || 8080);
  const { server } = createApp();
  server.listen(port, () => console.log(`CaptionGate at http://localhost:${port}`));
}
