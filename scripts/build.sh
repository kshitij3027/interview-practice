#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q aidlink.py aidlink_pkg tests
