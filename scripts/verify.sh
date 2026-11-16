#!/usr/bin/env bash
set -euo pipefail
python3 chronocheck.py check --clocks fixtures/clocks.csv --measurements fixtures/measurements.csv
python3 - <<'PY'
import json, subprocess, sys
from pathlib import Path
command = [sys.executable, 'chronocheck.py', 'audit', '--clocks', 'fixtures/clocks.csv', '--measurements', 'fixtures/measurements.csv', '--requests', 'fixtures/requests.jsonl']
p = subprocess.run(command, capture_output=True, text=True, check=True)
lines = p.stdout.splitlines()
assert len(lines) == len(Path('fixtures/requests.jsonl').read_text().splitlines())
assert all(isinstance(json.loads(row), dict) for row in lines)
assert not p.stderr
print('CLI smoke verification passed:', len(lines), 'request lines')
PY
