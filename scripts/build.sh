#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q market_book.py books tests
printf 'Python compilation passed\n'
