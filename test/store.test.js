import test from "node:test";
import assert from "node:assert/strict";
import { GrantStore } from "../src/store.js";

function store() { return GrantStore.fromFixtures(); }

test("list is deterministic, filtered, and cursor paginated", () => {
  const s = store();
  const first = s.list({ status: "pending", limit: 3 });
  assert.equal(first.items.length, 3);
  assert.ok(first.items.every((g) => g.status === "pending"));
  assert.ok(first.nextCursor);
  const second = s.list({ status: "pending", limit: 3, cursor: first.nextCursor });
  assert.equal(new Set([...first.items, ...second.items].map((g) => g.id)).size, 6);
  const keys = first.items.map((g) => `${g.system}|${g.principal}|${g.id}`);
  assert.deepEqual(keys, [...keys].sort());
});

test("note change increments grant and dataset revisions exactly once", () => {
  const s = store();
  const before = s.get("g-001");
  const result = s.updateNote("g-001", before.revision, "  reviewed by owner  ");
  assert.equal(result.kind, "ok");
  assert.equal(result.changed, true);
  assert.equal(result.grant.ownerNote, "reviewed by owner");
  assert.equal(result.grant.revision, before.revision + 1);
  assert.equal(result.datasetRevision, 2);
});

test("note no-op does not increment revisions", () => {
  const s = store();
  const before = s.get("g-001");
  const result = s.updateNote("g-001", before.revision, ` ${before.ownerNote} `);
  assert.equal(result.kind, "ok");
  assert.equal(result.changed, false);
  assert.equal(result.grant.revision, before.revision);
  assert.equal(result.datasetRevision, 1);
});

test("stale note change returns current state and does not mutate", () => {
  const s = store();
  const before = s.get("g-002");
  const result = s.updateNote("g-002", before.revision + 4, "new note");
  assert.equal(result.kind, "stale");
  assert.deepEqual(s.get("g-002"), before);
  assert.equal(s.meta().datasetRevision, 1);
});
