#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q signalgate.py signalgate_pkg tests
