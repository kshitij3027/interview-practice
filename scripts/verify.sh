#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 pulserank.py check --scopes fixtures/scopes.csv --observations fixtures/observations.csv
python3 - <<'PY'
import json
import subprocess
from pathlib import Path
queries = Path('fixtures/queries.jsonl').read_text(encoding='utf-8').splitlines()
completed = subprocess.run(['python3','pulserank.py','audit','--scopes','fixtures/scopes.csv',
  '--observations','fixtures/observations.csv','--queries','fixtures/queries.jsonl'],
  text=True, capture_output=True, check=True)
rows = [json.loads(line) for line in completed.stdout.splitlines()]
assert len(rows) == len(queries), (len(rows), len(queries))
assert all(isinstance(row, dict) and 'status' in row and 'query_id' in row for row in rows)
assert rows[7]['reason'] == 'invalid_query'
assert rows[9]['reason'] == 'unknown_scope'
assert completed.stderr == ''
print(f'CLI smoke check OK: {len(rows)} responses')
PY
