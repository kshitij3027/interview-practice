import http from "node:http";
import { createHandler } from "./http.js";
import { GrantStore } from "./store.js";

export function createApp() {
  const store = GrantStore.fromFixtures();
  return { store, server: http.createServer(createHandler(store)) };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const port = Number(process.env.PORT || 8080);
  const { server } = createApp();
  server.listen(port, "127.0.0.1", () => {
    console.log(`AccessQ listening on http://127.0.0.1:${port}`);
  });
}
