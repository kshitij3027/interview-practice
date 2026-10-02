#!/usr/bin/env bash
set -euo pipefail

output="$(node suggest.js validate --terms fixtures/terms.csv --aliases fixtures/aliases.csv --queries fixtures/queries.jsonl)"

node -e '
const value = JSON.parse(process.argv[1]);
if (
  value.terms !== 11 ||
  value.aliases !== 9 ||
  value.queries !== 10 ||
  value.valid_queries !== 9 ||
  value.invalid_queries !== 1
) {
  throw new Error("unexpected fixture summary: " + process.argv[1]);
}
console.log(
  "fixture verification passed: " +
    value.terms +
    " terms / " +
    value.aliases +
    " aliases / " +
    value.queries +
    " queries"
);
' "$output"
