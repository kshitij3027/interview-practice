#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 claimsignal.py validate --rules fixtures/rules.csv --cases fixtures/cases.jsonl
python3 - <<'PY'
from claimsignal.data import iter_case_requests, load_rules
rules = load_rules('fixtures/rules.csv')
requests = list(iter_case_requests('fixtures/cases.jsonl'))
assert len(rules) == 19
assert len(requests) == 13
assert sum(case is None for case, _ in requests) == 3
assert any(rule.phrase == 'gas-smell' for rule in rules)
print('verification fixtures parsed')
PY
