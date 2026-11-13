#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q tracecode tracecode.py tests
printf 'Python syntax OK\n'
