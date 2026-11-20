import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from freshclaim.catalog import CatalogError, load_lots
from freshclaim.cli import parse_request
from freshclaim.engine import FreshClaim

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    def test_catalog_deduplicates_replays(self):
        inventory = load_lots(ROOT / "fixtures/lots.csv")
        self.assertEqual(len(inventory[("OAK", "APPLE")]), 6)
        self.assertEqual(inventory[("OAK", "APPLE")][0].lot_id, "O-A1")

    def test_conflicting_lots_are_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "lots.csv"
            path.write_text("lot_id,store_id,sku,ready_min,expiry_min,units\nL,A,B,0,3,1\nL,A,B,0,3,2\n")
            with self.assertRaises(CatalogError):
                load_lots(path)

    def test_numeric_csv_validation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "lots.csv"
            path.write_text("lot_id,store_id,sku,ready_min,expiry_min,units\nL,A,B,00,3,1\n")
            with self.assertRaises(CatalogError):
                load_lots(path)

    def test_request_validation_and_id_recovery(self):
        req, error = parse_request('{"request_id":"q1","store_id":"OAK","sku":"APPLE","orders":[{"order_id":"a","pickup_min":true,"units":2}]}')
        self.assertIsNone(req)
        self.assertEqual(error["request_id"], "q1")
        self.assertEqual(error["reason"], "invalid_query")

    def test_empty_and_unique_orders(self):
        req, error = parse_request('{"request_id":"q","store_id":"OAK","sku":"APPLE","orders":[]}')
        self.assertIsNone(error)
        self.assertEqual(req["orders"], [])
        req, error = parse_request('{"request_id":"q","store_id":"OAK","sku":"APPLE","orders":[{"order_id":"a","pickup_min":3,"units":1},{"order_id":"a","pickup_min":4,"units":2}]}')
        self.assertIsNone(req)
        self.assertEqual(error["reason"], "invalid_query")

    def test_deliberate_implementation_gap(self):
        inventory = load_lots(ROOT / "fixtures/lots.csv")
        req, err = parse_request('{"request_id":"q","store_id":"OAK","sku":"APPLE","orders":[]}')
        self.assertIsNone(err)
        result = FreshClaim(inventory).assess(req)
        self.assertIn(result["status"], ("not_implemented", "ok"))

    def test_check_cli(self):
        run = subprocess.run(["python3", "freshclaim.py", "check", "--lots", "fixtures/lots.csv"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('"unique_lots":20', run.stdout)

    def test_batch_errors_do_not_stop_following_requests(self):
        run = subprocess.run(["python3", "freshclaim.py", "assess", "--lots", "fixtures/lots.csv", "--requests", "fixtures/requests.jsonl"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(run.stdout.splitlines()), 12)
        self.assertIn('"reason":"unknown_stock"', run.stdout)
        self.assertIn('"reason":"invalid_query"', run.stdout)


if __name__ == "__main__":
    unittest.main()
