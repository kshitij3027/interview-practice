#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m py_compile queuepulse.py queuepulse_cli.py tests/test_starter.py
printf 'Python compilation passed\n'
