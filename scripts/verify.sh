#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tracecode.py check --models fixtures/models.csv --ranges fixtures/ranges.csv
python3 tracecode.py recover --models fixtures/models.csv --ranges fixtures/ranges.csv --scans fixtures/scans.jsonl | python3 -c '
import json,sys
rows=[json.loads(line) for line in sys.stdin]
assert len(rows)==12, len(rows)
assert rows[0]["status"]=="not_implemented"
assert rows[-1]["status"]=="not_implemented"
assert any(r["status"]=="invalid" for r in rows)
print("JSONL CLI smoke verification OK: %d records"%len(rows))
'
