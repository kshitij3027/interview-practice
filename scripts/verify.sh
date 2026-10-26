#!/usr/bin/env bash
set -euo pipefail
python3 yardpulse.py validate --yards fixtures/yards.csv --containers fixtures/containers.csv --links fixtures/links.csv --events fixtures/events.csv --queries fixtures/queries.jsonl
python3 yardpulse.py resolve --yards fixtures/yards.csv --containers fixtures/containers.csv --links fixtures/links.csv --events fixtures/events.csv --queries fixtures/queries.jsonl | python3 -c 'import sys,json; rows=[json.loads(line) for line in sys.stdin]; assert len(rows)==17; print("JSONL scaffold verified:",len(rows),"records")'
