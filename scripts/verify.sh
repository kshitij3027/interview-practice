#!/usr/bin/env bash
set -euo pipefail
python3 -B coverguard.py --scopes fixtures/scopes.csv --probes fixtures/probes.csv --observations fixtures/observations.csv --audits fixtures/audits.jsonl | python3 -B -c 'import sys,json; rows=[json.loads(line) for line in sys.stdin]; assert len(rows)==23, len(rows); assert rows[0]["audit_id"]=="A01" and rows[0]["status"] in ("unimplemented","ok"); assert rows[10]["reason"]=="invalid_audit"; assert rows[12]["reason"]=="unknown_scope"; assert rows[13]["reason"]=="invalid_audit"; print("CLI wiring verified: 23 JSONL records")'
