#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 sourcemark.py check --lots fixtures/lots.csv --mixes fixtures/mixes.csv --membership fixtures/membership.csv
python3 sourcemark.py assess --lots fixtures/lots.csv --mixes fixtures/mixes.csv --membership fixtures/membership.csv --requests fixtures/requests.jsonl | python3 -c 'import json,sys; a=[json.loads(x) for x in sys.stdin]; assert len(a)>=12; assert any(x["status"]=="invalid" for x in a); assert any(x["status"]=="not_implemented" for x in a); print("JSONL smoke verification passed")'
