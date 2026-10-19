"""Starter-harness tests, not solutions to the customer audit."""
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from uplink import InputError, load_assets, load_fragments, parse_query

ROOT = Path(__file__).resolve().parents[1]

class HarnessTests(unittest.TestCase):
    def test_manifest_and_fragment_fixture_load(self):
        assets = load_assets(ROOT / "fixtures/manifests.csv")
        fragments = load_fragments(ROOT / "fixtures/fragments.jsonl", assets)
        self.assertEqual(len(assets), 6)
        self.assertGreaterEqual(len(fragments), 10)
        self.assertTrue(any(f.data == b"HELLO" for f in fragments))

    def test_replay_is_not_double_counted(self):
        assets = load_assets(ROOT / "fixtures/manifests.csv")
        fragments = load_fragments(ROOT / "fixtures/fragments.jsonl", assets)
        ids = [f.capture_id for f in fragments]
        self.assertEqual(len(ids), len(set(ids)))

    def test_queries_reject_boolean_offsets(self):
        with self.assertRaises(ValueError):
            parse_query({"request_id":"q","kind":"read","asset_id":"A","start":True,"end":2})

    def test_duplicate_conflicting_capture_is_invalid(self):
        assets = load_assets(ROOT / "fixtures/manifests.csv")
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/"fragments.jsonl"
            line = {"capture_id":"same","asset_id":"A-STRIP","offset":0,
                    "payload_b64":base64.b64encode(b"HELLO").decode()}
            source.write_text(json.dumps(line)+"\n"+json.dumps({**line,"offset":1})+"\n")
            with self.assertRaises(InputError):
                load_fragments(source, assets)

    def test_validate_cli(self):
        p = subprocess.run([sys.executable, str(ROOT / "uplink.py"), "validate",
              "--manifests", str(ROOT / "fixtures/manifests.csv"),
              "--fragments", str(ROOT / "fixtures/fragments.jsonl"),
              "--queries", str(ROOT / "fixtures/queries.jsonl")],
              capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["assets"], 6)

if __name__ == "__main__":
    unittest.main()
