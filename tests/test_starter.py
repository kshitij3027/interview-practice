"""Starter contract tests; these intentionally do not test planning optimization."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aidlink_pkg.data import CatalogError, load_catalog, parse_request
from aidlink_pkg.planner import plan

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"


def load():
    return load_catalog(FIX / "depots.csv", FIX / "clinics.csv", FIX / "lanes.csv")


class StarterTests(unittest.TestCase):
    def test_fixture_catalog_loads_and_deduplicates(self):
        catalog = load()
        self.assertEqual((len(catalog.depots), len(catalog.clinics), len(catalog.lanes)), (5, 6, 14))
        self.assertEqual(catalog.lanes["L-03"].capacity, 6)

    def test_query_defaults(self):
        rid, request, err = parse_request('{"request_id":"A"}', load())
        self.assertEqual((rid, err), ("A", None))
        self.assertEqual((request.disabled_lanes, request.stock_overrides, request.need_overrides), (frozenset(), {}, {}))

    def test_query_disabled_duplicates(self):
        _, request, err = parse_request('{"request_id":"q","disabled_lanes":["L-05","L-05"]}', load())
        self.assertIsNone(err)
        self.assertEqual(request.disabled_lanes, frozenset({"L-05"}))

    def test_unknown_reference_is_per_query(self):
        rid, request, err = parse_request('{"request_id":"q","disabled_lanes":["unknown"]}', load())
        self.assertEqual((rid, request, err), ("q", None, "unknown_reference"))

    def test_bool_not_a_number(self):
        rid, request, err = parse_request('{"request_id":"q","stock_overrides":{"D-PORT":true}}', load())
        self.assertEqual((rid, request, err), ("q", None, "invalid_request"))

    def test_non_object_invalid(self):
        self.assertEqual(parse_request('[]', load()), (None, None, "invalid_request"))

    def test_conflicting_catalog_replay_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "depots.csv"
            path.write_text("depot_id,stock\nA,5\nA,6\n")
            with self.assertRaises(CatalogError):
                load_catalog(path, FIX / "clinics.csv", FIX / "lanes.csv")

    def test_check_command(self):
        result = subprocess.run([sys.executable, str(ROOT / "aidlink.py"), "check", "--depots", str(FIX / "depots.csv"), "--clinics", str(FIX / "clinics.csv"), "--lanes", str(FIX / "lanes.csv"), "--requests", str(FIX / "requests.jsonl")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["valid_requests"] + summary["invalid_requests"], 15)
        self.assertGreater(summary["invalid_requests"], 0)

    def test_planning_hook_is_unimplemented(self):
        _, request, err = parse_request('{"request_id":"q"}', load())
        self.assertIsNone(err)
        self.assertIsNone(plan(load(), request))


if __name__ == "__main__":
    unittest.main()
