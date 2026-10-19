#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 promise_clock.py check --coverage fixtures/coverage.csv --blackouts fixtures/blackouts.csv --tickets fixtures/tickets.csv --pauses fixtures/pauses.csv
python3 promise_clock.py assess --coverage fixtures/coverage.csv --blackouts fixtures/blackouts.csv --tickets fixtures/tickets.csv --pauses fixtures/pauses.csv --queries fixtures/queries.jsonl > /tmp/promiseclock_starter_verify_$$.jsonl
python3 - /tmp/promiseclock_starter_verify_$$.jsonl <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])]
assert len(rows) == 12
assert sum(r['status'] == 'invalid' for r in rows) == 4
assert sum(r['status'] == 'not_implemented' for r in rows) == 8
print('Starter request-stream verification passed: 12 rows (4 invalid)')
PY
rm -f /tmp/promiseclock_starter_verify_$$.jsonl
