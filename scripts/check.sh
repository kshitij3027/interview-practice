#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest -v
python3 planner.py --help >/dev/null
echo "baseline checks passed"
