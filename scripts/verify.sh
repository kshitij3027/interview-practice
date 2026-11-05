#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PYVER'
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from server.data import load_workspace, load_activity
root=Path('fixtures')
assert (root/'workspace.json').exists()
workspace=load_workspace(); feed=load_activity()
assert len(workspace['jobs'])==12 and len(workspace['sites'])==4
assert len(feed)>=20
assert all(job['status'] in {'in_progress','waiting_customer','resolved'} for job in workspace['jobs'])
assert all(site['timeZone'] and ZoneInfo(site['timeZone']) for site in workspace['sites'])
print(f"Fixture verification passed: {len(workspace['jobs'])} jobs, {len(workspace['sites'])} sites, {len(feed)} activity rows")
PYVER
