"""Input, output and error contracts for the practice task."""
import argparse
import json
import sys
from .catalog import CatalogError, load_lots, valid_id
from .engine import FreshClaim


def valid_int(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def parse_request(line):
    try:
        data = json.loads(line)
    except (ValueError, TypeError):
        return None, {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    recover = data.get("request_id") if isinstance(data, dict) else None
    if not valid_id(recover, request=True):
        recover = None
    invalid = {"request_id": recover, "status": "invalid", "reason": "invalid_query"}
    if not isinstance(data, dict) or recover is None:
        return None, invalid
    if not valid_id(data.get("store_id")) or not valid_id(data.get("sku")):
        return None, invalid
    orders = data.get("orders")
    if not isinstance(orders, list) or len(orders) > 12:
        return None, invalid
    seen = set()
    for order in orders:
        if not isinstance(order, dict):
            return None, invalid
        name = order.get("order_id")
        if not valid_id(name) or name in seen:
            return None, invalid
        seen.add(name)
        if not valid_int(order.get("pickup_min"), 0, 10**9) or not valid_int(order.get("units"), 1, 10**6):
            return None, invalid
    return data, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="FreshClaim stock promise assessor")
    sub = ap.add_subparsers(dest="command", required=True)
    for cmd in ("check", "assess"):
        parser = sub.add_parser(cmd)
        parser.add_argument("--lots", required=True)
        if cmd == "assess":
            parser.add_argument("--requests", required=True)
    args = ap.parse_args(argv)
    try:
        inventory = load_lots(args.lots)
        if args.command == "check":
            print(json.dumps({"status": "ok", "partitions": len(inventory), "unique_lots": sum(len(v) for v in inventory.values())}, separators=(",", ":")))
            return 0
        engine = FreshClaim(inventory)
        with open(args.requests, encoding="utf-8") as f:
            for line in f:
                request, error = parse_request(line)
                if error is not None:
                    result = error
                elif (request["store_id"], request["sku"]) not in inventory:
                    result = {"request_id": request["request_id"], "status": "invalid", "reason": "unknown_stock"}
                else:
                    result = engine.assess(request)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=True))
        return 0
    except (CatalogError, OSError, ValueError) as exc:
        print(f"FreshClaim error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
