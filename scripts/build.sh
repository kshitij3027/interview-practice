#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q promise_clock.py slaops tests
printf 'Python compilation passed\n'
