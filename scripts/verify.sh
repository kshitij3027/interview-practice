#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 dispatch.py --check-inputs
python3 dispatch.py --help >/dev/null
python3 dispatch.py | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin), dict)'
