"""CLI for the immutable marketplace snapshot; one output line per query."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data_io import load_listings, read_requests
from gallery import Gallery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MirrorTrace fingerprint candidate-retrieval exercise")
    parser.add_argument("--fixtures", type=Path, default=Path("fixtures"))
    parser.add_argument("--validate-only", action="store_true", help="validate listing snapshot and requests")
    args = parser.parse_args(argv)
    try:
        listings = load_listings(args.fixtures / "listings.csv")
        requests = list(read_requests(args.fixtures / "requests.jsonl"))
    except (OSError, ValueError) as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2

    if args.validate_only:
        print(json.dumps({"listings": len(listings), "requests": len(requests),
                          "invalid_requests": sum(err is not None for _, _, err in requests)}))
        return 0

    gallery = Gallery(listings)
    for request_id, query, error in requests:
        if error is not None:
            output = {"request_id": request_id, "status": "invalid_request", "error": error}
        else:
            try:
                matches = gallery.find(query)
            except NotImplementedError:
                output = {"request_id": request_id, "status": "not_implemented", "matches": []}
            else:
                output = {"request_id": request_id, "status": "resolved", "matches": [
                    {"listing_id": listing.listing_id, "bit_errors": errors, "risk_score": listing.risk_score}
                    for listing, errors in matches
                ]}
        print(json.dumps(output, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
