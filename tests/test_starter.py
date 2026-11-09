"""Smoke checks for the provided interfaces, not the customer capability."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vaultscope.data import InvalidCatalog, load_snapshot, parse_query
from vaultscope.engine import VaultScope

ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_snapshot(ROOT / "fixtures")

    def test_catalog_declarations(self):
        self.assertEqual(self.snapshot["users"]["alice"], "alpha")
        self.assertEqual(self.snapshot["resources"]["beta_report"], "beta")

    def test_history_loaded(self):
        self.assertGreater(len(self.snapshot["memberships"]), 10)
        self.assertGreater(len(self.snapshot["policies"]), 10)

    def test_query_structure(self):
        query, error = parse_query('{"query_id":"q","user_id":"alice","resource_id":"handbook","action":"view","at_ms":0}')
        self.assertIsNone(error)
        self.assertEqual(query["query_id"], "q")

    def test_bool_is_not_time(self):
        query, error = parse_query('{"query_id":"q","user_id":"alice","resource_id":"handbook","action":"view","at_ms":true}')
        self.assertIsNone(query)
        self.assertEqual(error["reason"], "invalid_query")

    def test_invalid_json_isolated(self):
        self.assertEqual(parse_query("{")[1]["status"], "invalid")

    def test_engine_contract_shape(self):
        audit = VaultScope(self.snapshot)
        response = audit.decide({"query_id": "q", "user_id": "alice", "resource_id": "handbook", "action": "view", "at_ms": 0})
        self.assertEqual(set(response), {"query_id", "status", "decision", "policy_id", "via"})

    def test_cli_line_count(self):
        process = subprocess.run([sys.executable, "vaultscope.py", "audit", "--catalog", "fixtures", "--queries", "fixtures/queries.jsonl"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(process.stdout.splitlines()), 14)
        self.assertTrue(all(isinstance(json.loads(line), dict) for line in process.stdout.splitlines()))

    def test_bad_catalog_fails_before_results(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory)
            for name in ("users", "groups", "resources", "memberships", "policies"):
                (sample / (name + ".csv")).write_bytes((ROOT / "fixtures" / (name + ".csv")).read_bytes())
            with (sample / "groups.csv").open("a") as stream:
                stream.write("ops,beta\n")
            with self.assertRaises(InvalidCatalog):
                load_snapshot(sample)


if __name__ == "__main__":
    unittest.main()
