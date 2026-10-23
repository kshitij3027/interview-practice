#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 main.py --fixtures fixtures --validate-only
python3 main.py --help >/dev/null
