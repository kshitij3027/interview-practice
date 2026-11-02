#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json
import subprocess
import sys
from pathlib import Path
p = subprocess.run([sys.executable, 'review.py', '--zones', 'fixtures/zones.jsonl', '--queries', 'fixtures/queries.jsonl'], capture_output=True, text=True, check=True)
rows = [json.loads(line) for line in p.stdout.splitlines()]
assert len(rows) == len(Path('fixtures/queries.jsonl').read_text().splitlines())
assert all(row['status'] in ('ok', 'error') for row in rows)
assert any(row['status'] == 'ok' for row in rows)
assert any(row['status'] == 'error' for row in rows)
print(f'CLI structure OK: {len(rows)} query lines; does not verify matching correctness')
PY
