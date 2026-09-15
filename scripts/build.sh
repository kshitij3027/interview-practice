#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q app server.py tests
node --check web/api.js
node --check web/store.js
node --check web/app.js
python3 - <<'PY'
from pathlib import Path
from app.store import CampaignStore
root = Path.cwd()
store = CampaignStore(root / 'fixtures')
assert len(store.campaigns) == 4
assert len(store.budget_changes) == 7
assert len(store.spend_events) >= 10
print(f"Build verified: {len(store.campaigns)} campaigns / {len(store.budget_changes)} budget changes / {len(store.spend_events)} spend rows")
PY
