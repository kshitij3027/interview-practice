#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q readiness gatequeue.py tests
echo "Python compilation passed"
