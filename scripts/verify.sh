#!/usr/bin/env bash
set -euo pipefail
python3 market_book.py validate --events fixtures/updates.csv --queries fixtures/queries.jsonl
