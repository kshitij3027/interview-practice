#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q yardpulse.py yardkit tests
echo 'Python compilation passed'
