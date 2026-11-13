#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -B -m py_compile waterline.py tests/test_starter.py
