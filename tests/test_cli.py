from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_help(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "cargo_recovery.py"), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("cargo screening-lane outage recovery", completed.stdout)

    def test_validate_fixture(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "cargo_recovery.py"),
                "validate",
                "--lanes",
                str(ROOT / "fixtures" / "lanes.csv"),
                "--bookings",
                str(ROOT / "fixtures" / "bookings.csv"),
                "--outages",
                str(ROOT / "fixtures" / "outages.jsonl"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual("ok", payload["status"])
        self.assertEqual(16, payload["bookings"])


if __name__ == "__main__":
    unittest.main()
