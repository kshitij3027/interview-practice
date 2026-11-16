#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile chronocheck.py tests/test_starter.py
