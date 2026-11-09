#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json
import subprocess
import sys
from pathlib import Path
p = subprocess.run([sys.executable, "vaultscope.py", "audit", "--catalog", "fixtures", "--queries", "fixtures/queries.jsonl"], capture_output=True, text=True)
assert p.returncode == 0, p.stderr
rows = [json.loads(x) for x in p.stdout.splitlines()]
assert len(rows) == len(Path("fixtures/queries.jsonl").read_text().splitlines())
assert rows[7]["reason"] == "tenant_mismatch"
assert rows[8]["reason"] == "unknown_entity"
assert rows[9]["reason"] == "invalid_query"
assert rows[11]["reason"] == "invalid_query"
assert all(isinstance(row, dict) for row in rows)
print(f"Fixture/CLI baseline verified: {len(rows)} request lines")
PY
