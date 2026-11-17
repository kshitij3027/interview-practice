#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('fixtures/workspace.json')
d = json.loads(p.read_text())
assert len(d['organizations']) == 3
assert len(d['cases']) >= 12
assert len({c['id'] for c in d['cases']}) == len(d['cases'])
assert {c['orgId'] for c in d['cases']} <= {o['id'] for o in d['organizations']}
print(f"Fixture: {len(d['organizations'])} organizations, {len(d['customers'])} customers, {len(d['cases'])} cases")
PY
if command -v node >/dev/null; then node --check web/app.js; fi
go vet ./...
go test ./...
