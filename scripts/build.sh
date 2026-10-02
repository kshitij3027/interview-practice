#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q locker_search.py locator tests
printf 'Python compilation passed\n'
