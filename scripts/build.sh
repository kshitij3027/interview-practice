#!/usr/bin/env bash
set -euo pipefail
python3 -B -m compileall -q freshclaim.py freshclaim tests
