import json
import tempfile
import unittest
from pathlib import Path

from locator.loader import DataValidationError, load_lockers, load_queries

ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def test_fixture_loads(self):
        lockers = load_lockers(ROOT / "fixtures" / "lockers.csv")
        self.assertEqual(len(lockers), 13)
        market = next(x for x in lockers if x.locker_id == "sf-market-b")
        self.assertEqual(market.capabilities, frozenset({"returns", "qr", "cold"}))

    def test_query_level_invalid_records_do_not_abort_file(self):
        records = load_queries(ROOT / "fixtures" / "queries.jsonl")
        self.assertEqual(len(records), 8)
        self.assertEqual(sum(1 for r in records if r.query is None), 2)
        self.assertIsNotNone(records[-3].query)

    def test_duplicate_required_capabilities_collapse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queries.jsonl"
            path.write_text(json.dumps({"request_id":"q","lat":0,"lon":0,"parcel_size":"S","required_capabilities":["returns","returns"],"max_distance_meters":10,"limit":1}) + "\n", encoding="utf-8")
            record = load_queries(path)[0]
            self.assertEqual(record.query.required_capabilities, frozenset({"returns"}))

    def test_duplicate_locker_id_fails_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lockers.csv"
            path.write_text("locker_id,lat,lon,status,max_parcel_size,available_slots,queue_minutes,capabilities\n" "dup,0,0,active,S,1,0,returns\n" "dup,1,1,active,S,1,0,returns\n", encoding="utf-8")
            with self.assertRaises(DataValidationError):
                load_lockers(path)


if __name__ == "__main__":
    unittest.main()
