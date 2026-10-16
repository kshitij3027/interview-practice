"""ScanLedger CLI: read one route catalog, audit independent JSONL scan tapes."""
from __future__ import annotations
import argparse
import json
import sys
from tracekit.auditor import ScanAuditor
from tracekit.reader import load_routes, parse_request, preserved_request_id

def process_line(raw: str, routes: dict, auditor: ScanAuditor) -> dict:
    payload = None
    try:
        payload = json.loads(raw)
        req = parse_request(payload)
    except (json.JSONDecodeError, ValueError):
        return {"request_id": preserved_request_id(payload), "status": "invalid", "reason": "invalid_query"}
    if req.route_id not in routes:
        return {"request_id": req.request_id, "status": "invalid", "reason": "unknown_route"}
    repairs = auditor.reconcile(routes[req.route_id], req.scans, req.max_repairs)
    if repairs is None:
        return {"request_id": req.request_id, "status": "unrepairable", "route_id": req.route_id, "max_repairs": req.max_repairs}
    return {"request_id": req.request_id, "status": "reconciled", "route_id": req.route_id, "repair_count": len(repairs), "repairs": repairs}

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit shipment checkpoint scan tapes")
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("validate", "reconcile"):
        command = sub.add_parser(action)
        command.add_argument("--routes", required=True)
        if action == "reconcile":
            command.add_argument("--observations", required=True)
    args = parser.parse_args()
    try:
        routes = load_routes(args.routes)
        if args.action == "validate":
            print(f"Catalog OK: {len(routes)} unique routes", file=sys.stderr)
            return 0
        auditor = ScanAuditor()
        with open(args.observations, encoding="utf-8") as stream:
            for line in stream:
                print(json.dumps(process_line(line, routes, auditor), separators=(",", ":")))
    except (OSError, ValueError) as exc:
        print(f"ScanLedger: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
