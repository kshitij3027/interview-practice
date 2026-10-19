#!/usr/bin/env bash
set -euo pipefail
bash scripts/build.sh
bash scripts/test.sh
python3 uplink.py validate --manifests fixtures/manifests.csv --fragments fixtures/fragments.jsonl --queries fixtures/queries.jsonl
python3 uplink.py --help >/dev/null
