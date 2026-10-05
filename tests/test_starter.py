from pathlib import Path
import unittest

from queuepulse import format_utc, load_queries, load_snapshot, parse_rfc3339

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = load_snapshot(ROOT / "fixtures/queues.csv", ROOT / "fixtures/events.csv")

    def test_snapshot_counts(self) -> None:
        self.assertEqual(4, len(self.snapshot.queues))
        self.assertEqual(18, self.snapshot.raw_revision_rows)
        self.assertEqual(14, self.snapshot.effective_posted_events)

    def test_highest_revision_wins_and_void_disappears(self) -> None:
        alpha = self.snapshot.effective_events_by_queue["q-alpha"]
        by_id = {event.event_id: event for event in alpha}
        self.assertEqual(6, by_id["a-103"].delta_items)
        self.assertNotIn("a-105", by_id)

    def test_exact_duplicate_revision_is_deduplicated(self) -> None:
        beta = self.snapshot.effective_events_by_queue["q-beta"]
        self.assertEqual(1, [event.event_id for event in beta].count("b-4"))

    def test_offset_equivalence(self) -> None:
        a = parse_rfc3339("2026-10-05T10:40:00Z")
        b = parse_rfc3339("2026-10-05T03:40:00-07:00")
        self.assertEqual(a, b)
        self.assertEqual("2026-10-05T10:40:00Z", format_utc(b))

    def test_bad_query_stays_local(self) -> None:
        queries = load_queries(ROOT / "fixtures/queries.csv")
        self.assertEqual(10, len(queries))
        bad = [q for q in queries if q.error is not None]
        self.assertEqual(1, len(bad))
        self.assertEqual("q-invalid-window", bad[0].query_key)

    def test_offset_snapshot_normalizes(self) -> None:
        beta = self.snapshot.queues["q-beta"]
        self.assertEqual("2026-10-01T07:00:00Z", format_utc(beta.snapshot_start))


if __name__ == "__main__":
    unittest.main()
