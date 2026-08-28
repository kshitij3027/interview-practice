import tempfile
import unittest
from pathlib import Path

from merge_guard import canonical_key, load_events, load_records, load_separations


FIXTURES = Path(__file__).parent / "fixtures"


class BaselineTests(unittest.TestCase):
    def test_records_fixture_loads(self):
        records = load_records(FIXTURES / "records.csv")
        self.assertGreaterEqual(len(records), 10)
        self.assertIn("crm:100", records)

    def test_separations_are_symmetric_and_deduplicated(self):
        records = load_records(FIXTURES / "records.csv")
        pairs = load_separations(FIXTURES / "separations.csv", records)
        self.assertIn(("billing:901", "crm:100"), pairs)
        self.assertEqual(
            sum(1 for pair in pairs if set(pair) == {"billing:901", "crm:100"}),
            1,
        )

    def test_events_fixture_loads_and_preserves_order(self):
        records = load_records(FIXTURES / "records.csv")
        events = load_events(FIXTURES / "events.jsonl", records)
        self.assertEqual(events[0]["event_id"], "e-001")
        self.assertEqual(events[-1]["type"], "query")

    def test_canonical_key_prefers_quality_then_time_then_id(self):
        records = load_records(FIXTURES / "records.csv")
        ordered = sorted(
            [records["crm:100"], records["billing:900"], records["support:44"]],
            key=canonical_key,
        )
        self.assertEqual(ordered[0].record_id, "billing:900")

    def test_unknown_event_record_fails_fast(self):
        records = load_records(FIXTURES / "records.csv")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(
                '{"event_id":"bad","type":"query","record_id":"missing:1"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_events(path, records)


if __name__ == "__main__":
    unittest.main()
