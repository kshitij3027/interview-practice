import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = [sys.executable, str(ROOT / "pulserank.py")]
SOURCES = ["--scopes", str(ROOT / "fixtures/scopes.csv"), "--observations", str(ROOT / "fixtures/observations.csv")]


class CLITests(unittest.TestCase):
    def test_check_reports_fixture_summary(self):
        proc = subprocess.run(BASE + ["check"] + SOURCES, capture_output=True, text=True, check=True)
        info = json.loads(proc.stdout)
        self.assertEqual(info["scopes"], 8)
        self.assertEqual(info["rows"], 25)
        self.assertEqual(proc.stderr, "")

    def test_audit_emits_one_json_result_per_input_line(self):
        proc = subprocess.run(BASE + ["audit"] + SOURCES + ["--queries", str(ROOT / "fixtures/queries.jsonl")],
                              capture_output=True, text=True, check=True)
        lines = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(lines), 13)
        self.assertEqual(lines[0]["query_id"], "g-wide")
        self.assertEqual(lines[7]["reason"], "invalid_query")
        self.assertEqual(lines[9]["reason"], "unknown_scope")
        self.assertIsNone(lines[10]["query_id"])
        self.assertEqual(lines[-1]["query_id"], "empty-scope")
        self.assertEqual(proc.stderr, "")
