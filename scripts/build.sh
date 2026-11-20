#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q signalwatch.py signalwatch tests
printf 'Python syntax checks passed\n'
