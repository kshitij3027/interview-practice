from __future__ import annotations

import unittest
from pathlib import Path

from recovery import load_bookings, load_lanes, load_outages, validate_baseline

ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def test_fixture_counts_and_capabilities(self) -> None:
        lanes = load_lanes(ROOT / "fixtures" / "lanes.csv")
        bookings = load_bookings(ROOT / "fixtures" / "bookings.csv")
        outages = load_outages(ROOT / "fixtures" / "outages.jsonl")

        self.assertEqual(7, len(lanes))
        self.assertEqual(16, len(bookings))
        self.assertEqual(4, len(outages))
        self.assertIn("hazmat", lanes["JFK-04"].capabilities)
        self.assertNotIn("cold", lanes["JFK-05"].capabilities)

    def test_fixture_baseline_is_valid(self) -> None:
        lanes = load_lanes(ROOT / "fixtures" / "lanes.csv")
        bookings = load_bookings(ROOT / "fixtures" / "bookings.csv")
        outages = load_outages(ROOT / "fixtures" / "outages.jsonl")
        validate_baseline(lanes, bookings, outages)


if __name__ == "__main__":
    unittest.main()
