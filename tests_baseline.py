"""Baseline checks for input parsing and CLI only; feature tests are intentionally absent."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data_io import load_listings, parse_query, read_requests

ROOT = Path(__file__).parent


class BaselineTests(unittest.TestCase):
    def test_listing_fixture_loads(self):
        rows = load_listings(ROOT / "fixtures/listings.csv")
        self.assertGreaterEqual(len(rows), 10)
        self.assertEqual(len(rows), len({r.listing_id for r in rows}))

    def test_identical_replay_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "replays.csv"
            header = "listing_id,market,seller_id,first_seen_ms,last_seen_ms,fingerprint_hex,risk_score\n"
            row = "a,US,s,0,*," + "0" * 32 + ",35\n"
            file.write_text(header + row + row)
            self.assertEqual(len(load_listings(file)), 1)

    def test_conflicting_replay_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "conflicts.csv"
            header = "listing_id,market,seller_id,first_seen_ms,last_seen_ms,fingerprint_hex,risk_score\n"
            a = "a,US,s,0,*," + "0" * 32 + ",35\n"
            b = "a,US,s,0,*," + "0" * 32 + ",36\n"
            file.write_text(header + a + b)
            with self.assertRaises(ValueError):
                load_listings(file)

    def test_uppercase_fingerprint_and_boundaries(self):
        request = {"request_id": "case-1", "market": "US", "seller_id": "s",
                   "as_of_ms": 0, "fingerprint_hex": "F" * 32,
                   "max_bit_errors": 3, "limit": 20, "min_risk_score": 0}
        parsed = parse_query(request)
        self.assertEqual(parsed.fingerprint, (1 << 128) - 1)
        self.assertEqual(parsed.max_bit_errors, 3)

    def test_invalid_request_does_not_abort_stream(self):
        stream = list(read_requests(ROOT / "fixtures/requests.jsonl"))
        self.assertGreaterEqual(len(stream), 10)
        self.assertTrue(any(error is not None for _, _, error in stream))
        self.assertTrue(any(error is None for _, _, error in stream))

    def test_bool_is_not_integer(self):
        data = {"request_id": "x", "market": "US", "seller_id": "s", "as_of_ms": True,
                "fingerprint_hex": "0" * 32, "max_bit_errors": 0, "limit": 1, "min_risk_score": 0}
        with self.assertRaises(ValueError):
            parse_query(data)

    def test_validate_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / "main.py"),
                                 "--fixtures", str(ROOT / "fixtures"), "--validate-only"],
                                capture_output=True, text=True, check=True)
        self.assertGreater(json.loads(result.stdout)["listings"], 0)


if __name__ == "__main__":
    unittest.main()
