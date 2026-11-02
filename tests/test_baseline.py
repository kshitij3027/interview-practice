"""Starter behavior only; the requested replay capability is not tested here."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cachekit.engine import CacheReplay
from cachekit.io import Event, load_catalog, load_event_tape, number

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "fixtures"


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(F / "tenants.csv", F / "objects.csv")

    def test_catalog_and_replays(self):
        self.assertEqual(len(self.catalog.tenants), 3)
        self.assertEqual(len(self.catalog.objects), 9)
        self.assertEqual(self.catalog.objects["A-ZERO"].ttl_ms, 0)

    def test_canonical_numbers(self):
        self.assertEqual(number("0", 0, 10), 0)
        for value in ("01", "-1", "1.0", " 1", "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value, 0, 10)

    def test_tape_order_and_replay(self):
        entries, ordered = load_event_tape(F / "events.jsonl", self.catalog)
        self.assertEqual(len(entries), 25)
        self.assertEqual(len(ordered), 20)
        self.assertEqual(ordered[0].event_id, "E-01")
        self.assertEqual(ordered[1].event_id, "E-02")
        self.assertEqual(ordered[-1].event_id, "E-20")
        self.assertEqual(sum(isinstance(x, dict) for x in entries), 4)

    def test_bad_replay_fails_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "events.jsonl"
            f.write_text('\n'.join([
                '{"event_id":"x","at_ms":1,"sequence":1,"kind":"fetch","tenant_id":"TEN-ALPHA","object_id":"A-LOGO"}',
                '{"event_id":"x","at_ms":2,"sequence":1,"kind":"fetch","tenant_id":"TEN-ALPHA","object_id":"A-LOGO"}',
            ]) + '\n')
            with self.assertRaises(ValueError):
                load_event_tape(f, self.catalog)

    def test_validation_command(self):
        result = subprocess.run([sys.executable, str(ROOT / "cacheflow.py"), "validate",
            "--tenants", str(F / "tenants.csv"), "--objects", str(F / "objects.csv"),
            "--events", str(F / "events.jsonl"), "--capacity-kb", "12"],
            text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["unique_events"], 20)

    def test_replay_scaffold_is_runnable(self):
        result = CacheReplay(self.catalog, 12).apply(Event("test", 5, 1, "fetch", "TEN-ALPHA", "A-NEWS"))
        self.assertEqual(result["event_id"], "test")


if __name__ == "__main__":
    unittest.main()
