from __future__ import annotations

import argparse
import json
import sys

from recovery import RecoveryPlanner, load_bookings, load_lanes, load_outages, validate_baseline
from recovery.time_utils import format_utc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or plan cargo screening-lane outage recovery")
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="validate the supplied baseline fixtures")
    _add_data_args(validate)

    plan = subparsers.add_parser("plan", help="plan every outage in the supplied JSONL file")
    _add_data_args(plan)
    return parser


def _add_data_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lanes", required=True)
    parser.add_argument("--bookings", required=True)
    parser.add_argument("--outages", required=True)


def load_all(args: argparse.Namespace):
    lanes = load_lanes(args.lanes)
    bookings = load_bookings(args.bookings)
    outages = load_outages(args.outages)
    validate_baseline(lanes, bookings, outages)
    return lanes, bookings, outages


def plan_to_json(plan) -> dict[str, object]:
    return {
        "outage_id": plan.outage_id,
        "assignments": [
            {
                "shipment_id": item.shipment_id,
                "lane_id": item.lane_id,
                "slot_start": format_utc(item.slot_start),
            }
            for item in sorted(plan.assignments, key=lambda item: item.shipment_id)
        ],
        "unassigned": sorted(plan.unassigned),
        "assigned_priority": plan.assigned_priority,
        "assigned_count": plan.assigned_count,
        "total_displacement_minutes": plan.total_displacement_minutes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(raw_argv)
    if args.command is None:
        parser.print_help()
        return 0

    lanes, bookings, outages = load_all(args)
    if args.command == "validate":
        print(json.dumps({"lanes": len(lanes), "bookings": len(bookings), "outages": len(outages), "status": "ok"}))
        return 0

    planner = RecoveryPlanner(lanes, bookings)
    for outage in outages:
        print(json.dumps(plan_to_json(planner.plan(outage)), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
