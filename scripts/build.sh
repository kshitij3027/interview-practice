#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q vaultscope vaultscope.py tests
printf 'Python compilation passed\n'
