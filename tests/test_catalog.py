import tempfile
import unittest
from pathlib import Path

from books.catalog import load_updates
from books.queries import QuoteRequest, parse_query, read_queries


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(__file__).resolve().parent.parent

    def test_fixture_load_and_replay(self):
        rows = load_updates(self.base / "fixtures/updates.csv")
        self.assertEqual(len(rows), 17)
        self.assertEqual({r.market for r in rows}, {"BOLTS", "CHIPS"})
        self.assertEqual(rows, sorted(rows, key=lambda r: (r.received_ms, r.sequence)))

    def test_conflicting_replay_rejected(self):
        original = (self.base / "fixtures/updates.csv").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(original + "u01,2000,8,CHIPS,A1,ask,150,5\n")
            with self.assertRaisesRegex(ValueError, "conflicting update_id"):
                load_updates(path)

    def test_colliding_sequence_rejected(self):
        original = (self.base / "fixtures/updates.csv").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(original + "u18,1000,1,CHIPS,A9,ask,151,1\n")
            with self.assertRaisesRegex(ValueError, "colliding event order"):
                load_updates(path)

    def test_owner_must_stay_fixed(self):
        original = (self.base / "fixtures/updates.csv").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(original + "u18,2000,1,BOLTS,A1,ask,151,1\n")
            with self.assertRaisesRegex(ValueError, "moved across market"):
                load_updates(path)

    def test_queries_baseline(self):
        rows = list(read_queries(self.base / "fixtures/queries.jsonl"))
        self.assertEqual(len(rows), 13)
        self.assertEqual(sum(isinstance(q, dict) for q in rows), 3)
        self.assertIsInstance(rows[0], QuoteRequest)

    def test_booleans_not_integer_timestamps(self):
        value = parse_query({"request_id": "hi", "market": "A", "as_of_ms": True, "action": "buy", "lots": 3})
        self.assertEqual(value, {"request_id": "hi", "status": "invalid", "reason": "invalid_query"})


if __name__ == "__main__":
    unittest.main()
