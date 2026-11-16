"""Green starter checks; these do not verify attribution correctness."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from sourcemark.catalog import Catalog, CatalogError
from sourcemark.contracts import QueryError, parse_query
from sourcemark.engine import SourceAttributor

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "fixtures"


def catalog():
    return Catalog.load(F / "lots.csv", F / "mixes.csv", F / "membership.csv")


class StarterTests(unittest.TestCase):
    def test_fixture_load(self):
        c = catalog()
        self.assertEqual(len(c.sites), 3)
        self.assertGreaterEqual(len(c.lots), 15)
        self.assertIn("MX-O0", c.membership)
        self.assertEqual(len(c.membership["MX-O0"]), 0)

    def test_duplicate_member_is_not_double_counted(self):
        c = catalog()
        self.assertEqual(len(c.membership["MX-O1"]), 3)

    def test_independent_valid_requests(self):
        c = catalog()
        q = parse_query({"request_id":"again", "site":"OAK", "max_sources":2, "readings":[{"mix_id":"MX-O1","result":"positive"},{"mix_id":"MX-O1","result":"positive"}]}, c)
        self.assertEqual(len(q.readings), 1)
        self.assertEqual(q.readings[0], ("MX-O1", "positive"))

    def test_long_request_id(self):
        c = catalog()
        ident = "r" * 128
        q = parse_query({"request_id": ident, "site": "OAK", "max_sources": 0, "readings": []}, c)
        self.assertEqual(q.request_id, ident)

    def test_query_rejects_boolean_limit(self):
        with self.assertRaises(QueryError) as ctx:
            parse_query({"request_id":"x", "site":"OAK", "max_sources":True, "readings":[]}, catalog())
        self.assertEqual(ctx.exception.reason, "invalid_query")

    def test_query_rejects_conflicting_repeats(self):
        raw = {"request_id":"r1", "site":"OAK", "max_sources":1, "readings":[{"mix_id":"MX-O1","result":"negative"},{"mix_id":"MX-O1","result":"positive"}]}
        with self.assertRaises(QueryError):
            parse_query(raw, catalog())

    def test_query_scoping(self):
        raw = {"request_id":"r1", "site":"OAK", "max_sources":1, "readings":[{"mix_id":"MX-R1","result":"positive"}]}
        with self.assertRaises(QueryError) as ctx:
            parse_query(raw, catalog())
        self.assertEqual(ctx.exception.reason, "wrong_site")

    def test_catalog_conflicts_are_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "lots.csv"
            p.write_text("lot_id,site,ingredient\nLOT-A01,OAK,wheat\nLOT-A01,RNO,wheat\n")
            with self.assertRaises(CatalogError):
                Catalog.load(p, F / "mixes.csv", F / "membership.csv")

    def test_engine_wired_but_unfinished(self):
        c = catalog()
        q = parse_query({"request_id":"demo", "site":"OAK", "max_sources":0, "readings":[]}, c)
        self.assertEqual(SourceAttributor(c).assess(q)["status"], "not_implemented")

    def test_check_command(self):
        cmd = [sys.executable, "sourcemark.py", "check", "--lots", "fixtures/lots.csv", "--mixes", "fixtures/mixes.csv", "--membership", "fixtures/membership.csv"]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["sites"], 3)

    def test_assess_emits_one_line_per_input(self):
        cmd = [sys.executable, "sourcemark.py", "assess", "--lots", "fixtures/lots.csv", "--mixes", "fixtures/mixes.csv", "--membership", "fixtures/membership.csv", "--requests", "fixtures/requests.jsonl"]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(run.stdout.splitlines()), len((F / "requests.jsonl").read_text().splitlines()))
        self.assertTrue(all(isinstance(json.loads(line), dict) for line in run.stdout.splitlines()))


if __name__ == "__main__":
    unittest.main()
