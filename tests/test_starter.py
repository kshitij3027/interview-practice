"""Starter-baseline checks only; write new tests for the actual lookup contract."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from airspace.engine import AirspaceReview
from airspace.io import CatalogError, QueryError, load_zones, parse_query, read_request_id

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    def test_catalog_loads_and_identical_replays_collapse(self):
        zones = load_zones(ROOT / "fixtures/zones.jsonl")
        self.assertGreaterEqual(len(zones), 10)
        self.assertEqual(len(zones), len({z.zone_id for z in zones}))

    def test_rings_are_tuples_and_winding_is_not_edited(self):
        zones = load_zones(ROOT / "fixtures/zones.jsonl")
        z = next(z for z in zones if z.zone_id == "bay_core")
        self.assertEqual(z.outer[0], (-100, -100))
        self.assertEqual(len(z.holes), 1)

    def test_query_parsing_rejects_bool_numeric(self):
        with self.assertRaises(QueryError):
            parse_query('{"request_id":"q","region":"bay","x":true,"y":0,"at_ms":20,"altitude_m":30}')
        q = parse_query('{"request_id":"q","region":"bay","x":-2,"y":0,"at_ms":20,"altitude_m":30}')
        self.assertEqual(q.limit, 3)

    def test_invalid_request_id_recovery(self):
        self.assertIsNone(read_request_id("not-json"))
        self.assertEqual(read_request_id('{"request_id":"bad","x":true}'), "bad")

    def test_conflicting_catalog_id_fails_as_snapshot(self):
        rows = (ROOT / "fixtures/zones.jsonl").read_text().splitlines()
        data = json.loads(rows[0]); data["priority"] += 1
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "zones.jsonl"
            p.write_text(rows[0] + "\n" + json.dumps(data) + "\n")
            with self.assertRaises(CatalogError):
                load_zones(p)

    def test_cli_preserves_one_output_per_query_line(self):
        proc = subprocess.run([sys.executable, str(ROOT / "review.py"), "--zones", str(ROOT / "fixtures/zones.jsonl"), "--queries", str(ROOT / "fixtures/queries.jsonl")], text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        outputs = [json.loads(line) for line in proc.stdout.splitlines()]
        input_count = len((ROOT / "fixtures/queries.jsonl").read_text().splitlines())
        self.assertEqual(len(outputs), input_count)
        self.assertTrue(any(row["status"] == "error" for row in outputs))
        self.assertTrue(any(row["status"] == "ok" for row in outputs))

    def test_select_interface_is_callable(self):
        engine = AirspaceReview(load_zones(ROOT / "fixtures/zones.jsonl"))
        query = parse_query('{"request_id":"q","region":"bay","x":0,"y":0,"at_ms":20,"altitude_m":30}')
        self.assertIsInstance(engine.select(query), list)


if __name__ == "__main__":
    unittest.main()
