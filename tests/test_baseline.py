"""Starter-only verification: IO contracts, not the candidate's audit logic."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from scan_audit import process_line
from tracekit.reader import load_routes, parse_request, preserved_request_id

ROOT = Path(__file__).resolve().parents[1]

class BaselineTest(unittest.TestCase):
    def test_fixture_catalog(self):
        routes = load_routes(ROOT / "fixtures/routes.csv")
        self.assertGreaterEqual(len(routes), 3)
        self.assertIn("HUB_A", routes["R-METRO-7"].sequence)
        self.assertEqual(routes["R-METRO-7"].sequence.count("HUB_A"), 2)

    def test_duplicate_route_replays_and_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "routes.csv"
            path.write_text("route_id,carrier,sequence\nR,Fast,AB|CD\nR,Fast,AB|CD\n")
            self.assertEqual(len(load_routes(path)), 1)
            path.write_text("route_id,carrier,sequence\nR,Fast,AB|CD\nR,Fast,AB|EF\n")
            with self.assertRaises(ValueError):
                load_routes(path)

    def test_request_parser_keeps_repeated_scans(self):
        req = parse_request({"request_id": "q", "route_id": "r", "scans": ["AA", "AA"], "max_repairs": 0})
        self.assertEqual(req.scans, ("AA", "AA"))

    def test_bool_budget_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_request({"request_id": "q", "route_id": "r", "scans": [], "max_repairs": False})

    def test_invalid_jsonl_preserves_request_id(self):
        self.assertEqual(preserved_request_id({"request_id": "ok", "scans": []}), "ok")
        self.assertIsNone(preserved_request_id({"request_id": 10}))
        self.assertEqual(process_line('{"request_id":"q","route_id":4}', {}, object()), {"request_id":"q","status":"invalid","reason":"invalid_query"})
        self.assertEqual(process_line('{', {}, object()), {"request_id":None,"status":"invalid","reason":"invalid_query"})

    def test_cli_catalog_validation(self):
        proc = subprocess.run([sys.executable, "scan_audit.py", "validate", "--routes", "fixtures/routes.csv"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertIn("Catalog OK", proc.stderr)

if __name__ == "__main__":
    unittest.main()
