#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 waterline.py --validate-only
python3 waterline.py --help >/dev/null
