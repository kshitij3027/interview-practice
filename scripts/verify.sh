#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from app.loaders import load_fixtures
endpoints, deliveries = load_fixtures()
assert len({e.id for e in endpoints}) == len(endpoints)
assert len({d.id for d in deliveries}) == len(deliveries)
print(f"verified {len(endpoints)} endpoints / {len(deliveries)} deliveries")
PY
