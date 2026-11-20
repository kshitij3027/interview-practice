"""Green baseline for existing loader, parser, and normalization only."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from signalwatch.catalog import load_catalog
from signalwatch.requests import Event, parse_event
from signalwatch.tokenize import tokens

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.tenants = ROOT / "fixtures/tenants.csv"
        self.signatures = ROOT / "fixtures/signatures.csv"

    def test_catalog_snapshot(self):
        catalog = load_catalog(self.tenants, self.signatures)
        self.assertEqual(set(catalog.tenants), {"NORTH", "SOUTH", "LAB"})
        by_id = {entry.signature_id: entry for entry in catalog.active}
        self.assertEqual(by_id["s-PAY"].phrase, "payment declined")
        self.assertNotIn("s-OLD", by_id)
        self.assertNotIn("s-TIME", by_id)

    def test_catalog_exact_replays(self):
        catalog = load_catalog(self.tenants, self.signatures)
        self.assertEqual(len(catalog.active), len({entry.signature_id for entry in catalog.active}))

    def test_catalog_conflicting_same_revision(self):
        value = self.signatures.read_text().replace("s-PAY,1,upsert,NORTH,payment rejected,7", "s-PAY,2,upsert,NORTH,payment rejected,7")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.csv"
            path.write_text(value)
            with self.assertRaises(ValueError):
                load_catalog(self.tenants, path)

    def test_tokenization(self):
        self.assertEqual(tokens("CARD--payment...declined!"), ("card", "payment", "declined"))
        self.assertEqual(tokens("code404 code 404"), ("code404", "code", "404"))

    def test_event_valid(self):
        result = parse_event('{"event_id":"e-1","tenant_id":"NORTH","text":"", "limit":0}')
        self.assertEqual(result, Event("e-1", "NORTH", "", 0))

    def test_event_limit_bool_invalid(self):
        result = parse_event('{"event_id":"e-1","tenant_id":"NORTH","text":"ok", "limit":true}')
        self.assertEqual(result, {"event_id": "e-1", "status": "invalid", "reason": "invalid_event"})

    def test_event_non_ascii_invalid(self):
        result = parse_event('{"event_id":"e-1","tenant_id":"NORTH","text":"café", "limit":1}')
        self.assertEqual(result["reason"], "invalid_event")

    def test_empty_input_invalid(self):
        self.assertEqual(parse_event("\n"), {"event_id": None, "status": "invalid", "reason": "invalid_event"})

    def test_cli_check(self):
        run = subprocess.run([sys.executable, str(ROOT / "signalwatch.py"), "check", "--tenants", str(self.tenants), "--signatures", str(self.signatures)], text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["tenants"], 3)

    def test_cli_invalid_lines(self):
        run = subprocess.run([sys.executable, str(ROOT / "signalwatch.py"), "scan", "--tenants", str(self.tenants), "--signatures", str(self.signatures), "--events", str(ROOT / "fixtures/invalid_only.jsonl")], text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([x["reason"] for x in result], ["invalid_event", "unknown_tenant", "invalid_event"])


if __name__ == "__main__":
    unittest.main()
