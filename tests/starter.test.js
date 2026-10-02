import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { parseCsv } from "../src/csv.js";
import { loadSnapshot } from "../src/catalog.js";
import { loadQueries, validateQuery } from "../src/queries.js";
import { codePointLength, normalizeText } from "../src/normalize.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function fixture(name) {
  return path.join(root, "fixtures", name);
}

test("normalization is shared and Unicode-aware", () => {
  assert.equal(normalizeText("  ＷIRELESS\tHeadPhones  "), "wireless headphones");
  assert.equal(codePointLength("é🙂"), 2);
});

test("CSV parser handles quoted commas and escaped quotes", () => {
  assert.deepEqual(
    parseCsv('a,b\n"x,y","z""q"\n'),
    [["a", "b"], ["x,y", 'z"q']]
  );
});

test("fixture snapshot loads and exact alias replay deduplicates", () => {
  const snapshot = loadSnapshot(fixture("terms.csv"), fixture("aliases.csv"));
  assert.equal(snapshot.terms.size, 11);
  assert.equal(snapshot.aliasCount, 9);
  assert.equal(snapshot.terms.get("t-001").aliases.length, 1);
});

test("query fixture parses with expected valid and invalid rows", () => {
  const queries = loadQueries(fixture("queries.jsonl"));
  const checks = queries.map(validateQuery);
  assert.equal(queries.length, 10);
  assert.equal(checks.filter((item) => item.ok).length, 9);
  assert.equal(checks.filter((item) => !item.ok).length, 1);
});

test("query validation enforces edit and limit bounds", () => {
  assert.equal(validateQuery({
    request_id: "q",
    locale: "en-US",
    text: "wire",
    max_edits: 2,
    limit: 10
  }).ok, true);

  assert.equal(validateQuery({
    request_id: "q",
    locale: "en-US",
    text: "wire",
    max_edits: 3,
    limit: 10
  }).ok, false);

  assert.equal(validateQuery({
    request_id: "q",
    locale: "en-US",
    text: "wire",
    max_edits: 1,
    limit: 0
  }).ok, false);
});
