#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 batchpath.py validate --datasets fixtures/datasets.csv --links fixtures/links.csv
python3 - <<'PY'
from pathlib import Path
from batchpath.requests import parse_query
lines = Path('fixtures/queries.jsonl').read_text().splitlines()
assert len(lines) == 11
accepted = sum(1 for line in lines if parse_query(line)[0] is not None)
assert accepted == 7, (accepted, len(lines))
print(f'verified {len(lines)} query lines, {accepted} structurally valid')
PY
