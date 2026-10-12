import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_validate(self):
        command = [sys.executable, "bundleport.py", "validate", "--releases", "fixtures/releases.csv", "--requirements", "fixtures/requirements.csv", "--conflicts", "fixtures/conflicts.csv", "--requests", "fixtures/requests.jsonl"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        details = json.loads(result.stdout)
        self.assertGreater(details["releases"], 5)
        self.assertGreater(details["requests"], details["valid_requests"])


if __name__ == "__main__":
    unittest.main()
