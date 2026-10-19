#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile uplink.py replay_engine.py tests/test_baseline.py
