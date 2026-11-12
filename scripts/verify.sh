#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
import json
from pathlib import Path
source=json.loads(Path('fixtures/catalog.json').read_text())
assert len(source['organizations'])==3 and len(source['contracts'])==12
assert len({c['id'] for c in source['contracts']})==12
assert all(c['periodStart']<c['periodEnd'] for c in source['contracts'])
assert all(c['planId'] in {p['id'] for p in source['plans']} for c in source['contracts'])
print('Fixture verification passed: 3 organizations, 3 plans, 12 contracts')
PY
