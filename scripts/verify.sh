#!/usr/bin/env bash
set -euo pipefail
python3 gridpulse.py check-inputs --sites fixtures/sites.csv --sessions fixtures/sessions.csv
python3 gridpulse.py assess --sites fixtures/sites.csv --sessions fixtures/sessions.csv --queries fixtures/queries.jsonl > /tmp/gridpulse_baseline_$$.jsonl
python3 - /tmp/gridpulse_baseline_$$.jsonl <<'PY'
import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
assert len(lines) == 15
assert sum(r['status'] == 'invalid' for r in lines) == 4
assert sum(r['status'] == 'not_implemented' for r in lines) == 11
print('Fixture and CLI baseline verified: 15 responses, 4 invalid inputs')
PY
rm -f /tmp/gridpulse_baseline_$$.jsonl
