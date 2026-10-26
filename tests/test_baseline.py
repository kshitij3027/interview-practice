"""Starter checks for input handling, not the customer planning requirements."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from records import SnapshotError, load_snapshot

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def sample():
    return load_snapshot(FIXTURES / "pods.csv", FIXTURES / "responders.csv",
                         FIXTURES / "incidents.csv", FIXTURES / "routes.csv")


class Baseline(unittest.TestCase):
    def test_fixture_loading(self):
        snap = sample()
        self.assertGreater(len(snap.incidents), 5)
        self.assertGreater(len(snap.routes), 10)
        self.assertEqual(len(snap.routes), len({(r.incident_id, r.responder_id) for r in snap.routes}))

    def test_route_order_is_stable(self):
        snap = sample()
        self.assertEqual(list(snap.routes), sorted(snap.routes,
            key=lambda r: (r.incident_id, r.responder_id)))

    def test_conflicting_route_replay_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "routes.csv"
            original = (FIXTURES / "routes.csv").read_text()
            path.write_text(original + "P0-A,N-1,99\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(FIXTURES / "pods.csv", FIXTURES / "responders.csv",
                              FIXTURES / "incidents.csv", path)

    def test_cli_validation_mode(self):
        p = subprocess.run([sys.executable, "dispatch.py", "--check-inputs"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
        data = json.loads(p.stdout)
        self.assertEqual(data["status"], "valid_snapshot")
        self.assertEqual(p.stderr, "")

    def test_cli_delivers_json(self):
        p = subprocess.run([sys.executable, "dispatch.py"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIsInstance(json.loads(p.stdout), dict)
        self.assertEqual(p.stderr, "")


if __name__ == "__main__":
    unittest.main()
