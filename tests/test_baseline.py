"""Starter checks; they do NOT validate the absent matching implementation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from signalgate_pkg.catalog import CatalogError, load_catalog
from signalgate_pkg.requests import RequestError, parse_request
from signalgate_pkg.scanner import SignalScanner

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ROOT / "fixtures/regions.csv"
SIGNATURES = ROOT / "fixtures/signatures.csv"
REQUESTS = ROOT / "fixtures/requests.jsonl"


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(REGIONS, SIGNATURES)

    def test_catalog_fixture_loads_and_deduplicates_replay(self):
        self.assertEqual(len(self.catalog.regions), 3)
        self.assertEqual(len(self.catalog.signatures), 16)

    def test_catalog_rejects_conflicting_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "signatures.csv"
            contents = SIGNATURES.read_text()
            dest.write_text(contents + "SIG-A1,*,99,0,1000,616263,true\n")
            with self.assertRaises(CatalogError):
                load_catalog(REGIONS, dest)

    def test_request_decodes_binary_chunks(self):
        request = parse_request('{"request_id":"q","region":"east","seen_at_ms":0,"chunks_b64":["AA==","/w==",""]}', self.catalog.regions)
        self.assertEqual(request.chunks, (b"\x00", b"\xff", b""))
        self.assertEqual(request.limit, 5)

    def test_rejects_noncanonical_chunk_and_bool_timestamp(self):
        for raw in ('{"request_id":"r","region":"east","seen_at_ms":0,"chunks_b64":["YQ"]}',
                    '{"request_id":"r","region":"east","seen_at_ms":true,"chunks_b64":[""]}'):
            with self.subTest(raw=raw), self.assertRaises(RequestError) as err:
                parse_request(raw, self.catalog.regions)
            self.assertEqual(err.exception.reason, "invalid_request")

    def test_unknown_region_distinguished_from_malformed(self):
        with self.assertRaises(RequestError) as err:
            parse_request('{"request_id":"r","region":"missing","seen_at_ms":1,"chunks_b64":[""]}', self.catalog.regions)
        self.assertEqual(err.exception.reason, "unknown_region")

    def test_scan_hook_returns_request_scoped_result(self):
        request = parse_request('{"request_id":"r","region":"east","seen_at_ms":1,"chunks_b64":["YQ=="]}', self.catalog.regions)
        result = SignalScanner(self.catalog).scan(request)
        self.assertEqual(result["request_id"], "r")
        self.assertIn("status", result)

    def test_check_cli_stays_quiet_on_stdout(self):
        cmd = [sys.executable, str(ROOT / "signalgate.py"), "check", "--regions", str(REGIONS),
               "--signatures", str(SIGNATURES), "--requests", str(REQUESTS)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertIn("Snapshot OK", proc.stderr)


if __name__ == "__main__":
    unittest.main()
