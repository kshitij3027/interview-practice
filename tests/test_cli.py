import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARGS = ["--yards", "fixtures/yards.csv", "--containers", "fixtures/containers.csv", "--links", "fixtures/links.csv", "--events", "fixtures/events.csv", "--queries", "fixtures/queries.jsonl"]


class CliTests(unittest.TestCase):
    def invoke(self, mode):
        return subprocess.run([sys.executable, "yardpulse.py", mode, *ARGS], cwd=ROOT, text=True, capture_output=True)

    def test_validation(self):
        result = self.invoke("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("30 events", result.stdout)

    def test_resolution_scaffold(self):
        result = self.invoke("resolve")
        self.assertEqual(result.returncode, 0, result.stderr)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(records), len((ROOT / "fixtures/queries.jsonl").read_text().splitlines()))
        self.assertEqual(records[0]["status"], "not_implemented")
        self.assertEqual(records[-1]["reason"], "invalid_query")


if __name__ == "__main__":
    unittest.main()
