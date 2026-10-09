#!/usr/bin/env python3
"""ClaimSignal batch command-line entry point."""
from __future__ import annotations

import argparse
import json
import sys

from claimsignal.data import iter_case_requests, load_rules
from claimsignal.service import ClaimResolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claims evidence catalog processor")
    parser.add_argument("command", choices=["validate", "resolve"])
    parser.add_argument("--rules", required=True)
    parser.add_argument("--cases", required=True)
    args = parser.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        if args.command == "validate":
            valid = invalid = 0
            for case, _error in iter_case_requests(args.cases):
                if case is None:
                    invalid += 1
                else:
                    valid += 1
            print(f"validated {len(rules)} deduplicated catalog rules / {valid} valid cases / {invalid} invalid cases")
            return 0
        resolver = ClaimResolver(rules)
        for case, error in iter_case_requests(args.cases):
            result = error if case is None else resolver.resolve_case(case)
            print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
        return 0
    except (ValueError, OSError, NotImplementedError) as exc:
        print(f"claimsignal: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
