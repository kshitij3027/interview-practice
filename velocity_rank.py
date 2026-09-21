from __future__ import annotations

import argparse
import json
import sys

from burstrank import DataValidationError, VelocityResolver, load_dataset


def add_common_files(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--clients", required=True)
    parser.add_argument("--policies", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--queries", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="velocity_rank")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    add_common_files(validate)
    resolve = sub.add_parser("resolve")
    add_common_files(resolve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        dataset = load_dataset(args.clients, args.policies, args.events, args.queries)
        if args.command == "validate":
            print(
                f"validated {len(dataset.clients)} clients / {len(dataset.policies)} policies / "
                f"{len(dataset.events)} deduplicated events / {len(dataset.queries)} queries"
            )
            return 0
        for result in VelocityResolver(dataset).resolve_all():
            print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0
    except DataValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
