import json
import tempfile
import unittest
from datetime import timezone
from pathlib import Path

from risk_pulse import Event, MerchantPolicy, iter_events, load_policies, parse_event, parse_timestamp


class BaselineHarnessTests(unittest.TestCase):
    def test_parse_timestamp_normalizes_to_utc(self):
        parsed = parse_timestamp("2026-08-31T12:00:00-04:00")
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-08-31T16:00:00+00:00")

    def test_parse_timestamp_rejects_timezone_less_value(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2026-08-31T16:00:00")

    def test_load_policies_reads_positive_integer_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "merchants.csv"
            path.write_text(
                "merchant_id,window_seconds,min_declines,min_distinct_cards,cooldown_seconds\n"
                "m-1,300,4,3,120\n",
                encoding="utf-8",
            )
            policies = load_policies(path)
        self.assertEqual(
            policies["m-1"],
            MerchantPolicy("m-1", 300, 4, 3, 120),
        )

    def test_parse_event_rejects_unknown_outcome(self):
        payload = {
            "event_id": "e-1",
            "source_partition": "p-1",
            "source_seq": 0,
            "merchant_id": "m-1",
            "occurred_at": "2026-08-31T16:00:00Z",
            "card_fingerprint": "card-a",
            "outcome": "timeout",
        }
        with self.assertRaises(ValueError):
            parse_event(payload, 1)

    def test_iter_events_parses_jsonl(self):
        payload = {
            "event_id": "e-1",
            "source_partition": "p-1",
            "source_seq": 3,
            "merchant_id": "m-1",
            "occurred_at": "2026-08-31T16:00:00Z",
            "card_fingerprint": "card-a",
            "outcome": "declined",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            events = list(iter_events(path))
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], Event)
        self.assertEqual(events[0].source_seq, 3)


if __name__ == "__main__":
    unittest.main()
