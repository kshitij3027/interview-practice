#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 fiber_ops.py check --sites fixtures/sites.csv --spans fixtures/spans.csv
python3 fiber_ops.py assess --sites fixtures/sites.csv --spans fixtures/spans.csv --queries fixtures/requests.jsonl >/tmp/fiberwatch-starter-check-$$.jsonl
python3 - <<'PY' /tmp/fiberwatch-starter-check-$$.jsonl
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    records = [json.loads(line) for line in f]
assert len(records) == 12
assert sum(r['status'] == 'invalid' for r in records) == 4
print('stream check:', len(records), 'requests, 4 query errors')
PY
rm -f /tmp/fiberwatch-starter-check-$$.jsonl
