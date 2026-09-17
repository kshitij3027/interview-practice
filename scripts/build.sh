#!/usr/bin/env bash
set -euo pipefail
go test ./...
go build ./...
node --check web/api.js
node --check web/store.js
node --check web/app.js
python3 - <<'PY'
import csv, json
with open('fixtures/returns.json') as f: rows=json.load(f)
assert len(rows)==6
with open('fixtures/carrier_scans.csv', newline='') as f: scans=list(csv.DictReader(f))
assert len(scans)==15
assert sorted({r['batch_id'] for r in scans})==['BATCH-0916-A','BATCH-0916-B','BATCH-0916-C']
print(f'fixture verification passed: {len(rows)} returns / {len(scans)} scan rows / 3 batches')
PY
