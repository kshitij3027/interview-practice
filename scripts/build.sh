#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q velocity_rank.py burstrank tests
python3 velocity_rank.py --help >/dev/null
