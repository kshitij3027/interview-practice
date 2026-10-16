#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q scan_audit.py tracekit tests
