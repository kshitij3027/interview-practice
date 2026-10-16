import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_snapshot_check_command(self):
        completed = subprocess.run([sys.executable, "fiber_ops.py", "check", "--sites", "fixtures/sites.csv", "--spans", "fixtures/spans.csv"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(completed.stdout)["spans"], 19)

    def test_stream_continues_after_bad_rows(self):
        completed = subprocess.run([sys.executable, "fiber_ops.py", "assess", "--sites", "fixtures/sites.csv", "--spans", "fixtures/spans.csv", "--queries", "fixtures/requests.jsonl"], cwd=ROOT, text=True, capture_output=True, check=True)
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["request_id"], "q-a")
        self.assertEqual(rows[8]["status"], "invalid")
        self.assertEqual(rows[9]["reason"], "unknown_span")
        self.assertIsNone(rows[11]["request_id"])


if __name__ == "__main__":
    unittest.main()

