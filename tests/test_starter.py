from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from burstrank.io import DataValidationError, load_dataset, load_events, load_clients, parse_instant


ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    def test_equivalent_offsets_parse_to_same_instant(self):
        self.assertEqual(
            parse_instant("2026-09-21T10:05:00Z"),
            parse_instant("2026-09-21T12:05:00+02:00"),
        )

    def test_fixture_dataset_loads_and_deduplicates_exact_event_retry(self):
        dataset = load_dataset(
            ROOT / "fixtures/clients.csv",
            ROOT / "fixtures/policies.csv",
            ROOT / "fixtures/events.csv",
            ROOT / "fixtures/queries.jsonl",
        )
        self.assertEqual(8, len(dataset.clients))
        self.assertEqual(3, len(dataset.policies))
        self.assertEqual(17, len(dataset.events))
        self.assertEqual(8, len(dataset.queries))

    def test_query_input_order_is_preserved_by_loader(self):
        dataset = load_dataset(
            ROOT / "fixtures/clients.csv",
            ROOT / "fixtures/policies.csv",
            ROOT / "fixtures/events.csv",
            ROOT / "fixtures/queries.jsonl",
        )
        self.assertEqual("q-us-later", dataset.queries[0].request_id)
        self.assertEqual("q-eu-offset", dataset.queries[1].request_id)

    def test_conflicting_event_id_is_rejected(self):
        clients = load_clients(ROOT / "fixtures/clients.csv")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.csv"
            path.write_text(
                "event_id,client_id,credential_id,occurred_at\n"
                "dup,c-a,x,2026-09-21T10:00:00Z\n"
                "dup,c-a,y,2026-09-21T10:00:00Z\n",
                encoding="utf-8",
            )
            with self.assertRaises(DataValidationError):
                load_events(path, clients)

    def test_naive_timestamp_without_offset_is_rejected(self):
        with self.assertRaises(DataValidationError):
            parse_instant("2026-09-21T10:00:00")


if __name__ == "__main__":
    unittest.main()
