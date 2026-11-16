#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q sourcemark.py sourcemark tests
