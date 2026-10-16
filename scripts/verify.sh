#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 scan_audit.py --help >/dev/null
python3 scan_audit.py reconcile --help >/dev/null
python3 scan_audit.py validate --routes fixtures/routes.csv >/dev/null
