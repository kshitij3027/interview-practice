#!/usr/bin/env bash
set -euo pipefail
./scripts/test.sh
./scripts/build.sh
python3 - <<'PY'
import csv
from datetime import datetime
from pathlib import Path
screens=list(csv.DictReader(Path("fixtures/screens.csv").open()))
windows=list(csv.DictReader(Path("fixtures/playlist_windows.csv").open()))
assert len(screens)==6
ids={s["id"] for s in screens}
assert len(ids)==len(screens)
assert len({w["window_id"] for w in windows})==len(windows)
for w in windows:
    assert w["screen_id"] in ids
    start=datetime.fromisoformat(w["start_at"].replace("Z","+00:00"))
    end=datetime.fromisoformat(w["end_at"].replace("Z","+00:00"))
    assert start<end
    assert 0<=int(w["priority"])<=9
    assert w["playlist_id"].strip()
    assert w["reason"].strip()
    assert w["state"] in {"active","cancelled"}
print(f"fixture verification passed: {len(screens)} screens / {len(windows)} playlist windows")
PY
