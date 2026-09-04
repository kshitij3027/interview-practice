from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recovery import load_bookings, load_lanes, load_outages, validate_baseline


def main() -> None:
    lanes = load_lanes(ROOT / "fixtures" / "lanes.csv")
    bookings = load_bookings(ROOT / "fixtures" / "bookings.csv")
    outages = load_outages(ROOT / "fixtures" / "outages.jsonl")
    validate_baseline(lanes, bookings, outages)
    print(f"fixture ok: {len(lanes)} lanes, {len(bookings)} bookings, {len(outages)} outages")


if __name__ == "__main__":
    main()
