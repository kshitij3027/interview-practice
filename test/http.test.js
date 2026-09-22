import test from "node:test";
import assert from "node:assert/strict";
import { createApp } from "../src/server.js";

async function withServer(fn) {
  const { server } = createApp();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  try { await fn(`http://127.0.0.1:${port}`); }
  finally { await new Promise((resolve) => server.close(resolve)); }
}

test("health, meta, and filtered grant list are reachable", async () => {
  await withServer(async (base) => {
    assert.deepEqual(await (await fetch(`${base}/api/health`)).json(), { ok: true });
    const meta = await (await fetch(`${base}/api/meta`)).json();
    assert.equal(meta.cycle.cycleId, "q3-2026");
    const response = await fetch(`${base}/api/grants?status=pending&system=crm&limit=2`);
    assert.equal(response.status, 200);
    const page = await response.json();
    assert.ok(page.items.every((g) => g.status === "pending" && g.system === "crm"));
  });
});

test("note endpoint enforces optimistic concurrency", async () => {
  await withServer(async (base) => {
    const detail = await (await fetch(`${base}/api/grants/g-003`)).json();
    const first = await fetch(`${base}/api/grants/g-003/note`, {
      method: "PATCH", headers: { "content-type": "application/json" },
      body: JSON.stringify({ expected_revision: detail.grant.revision, note: "ownership confirmed" }),
    });
    assert.equal(first.status, 200);
    const stale = await fetch(`${base}/api/grants/g-003/note`, {
      method: "PATCH", headers: { "content-type": "application/json" },
      body: JSON.stringify({ expected_revision: detail.grant.revision, note: "second writer" }),
    });
    assert.equal(stale.status, 409);
  });
});
