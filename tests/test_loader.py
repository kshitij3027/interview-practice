from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readiness.loader import DatasetError, load_queries, load_snapshot

ROOT = Path(__file__).resolve().parents[1]

class LoaderTests(unittest.TestCase):
    def test_fixture_snapshot_loads_and_deduplicates(self):
        snapshot = load_snapshot(
            ROOT / "fixtures/workflows.csv",
            ROOT / "fixtures/tasks.csv",
            ROOT / "fixtures/dependencies.csv",
            ROOT / "fixtures/events.csv",
        )
        self.assertEqual(2, len(snapshot.workflows))
        self.assertEqual(10, len(snapshot.tasks))
        self.assertEqual(9, len(snapshot.dependencies))
        self.assertEqual(11, len(snapshot.events))

    def test_queries_keep_file_order_and_parse_offsets_as_instants(self):
        queries = load_queries(ROOT / "fixtures/queries.jsonl")
        self.assertEqual(["q-001", "q-002", "q-003"], [q.request_id for q in queries[:3]])
        self.assertEqual(queries[1].as_of, queries[2].as_of)

    def test_malformed_query_is_local_to_that_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queries.jsonl"
            path.write_text(
                '{"request_id":"ok","workflow_id":"wf-payments","as_of":"2026-09-28T09:00:00Z","limit":2}\n'
                '{"request_id":"bad","workflow_id":"wf-payments","as_of":"nope","limit":2}\n'
                '{"request_id":"later","workflow_id":"wf-payments","as_of":"2026-09-28T09:10:00Z","limit":1}\n',
                encoding="utf-8",
            )
            queries = load_queries(path)
        self.assertTrue(queries[0].valid)
        self.assertFalse(queries[1].valid)
        self.assertTrue(queries[2].valid)

    def test_conflicting_event_id_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name in ("workflows.csv", "tasks.csv", "dependencies.csv"):
                (tmp / name).write_text(
                    (ROOT / "fixtures" / name).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            (tmp / "events.csv").write_text(
                "event_id,task_id,occurred_at,version,action\n"
                "e1,pay-isolate,2026-09-28T09:05:00Z,1,complete\n"
                "e1,pay-isolate,2026-09-28T09:06:00Z,1,complete\n",
                encoding="utf-8",
            )
            with self.assertRaises(DatasetError):
                load_snapshot(
                    tmp / "workflows.csv",
                    tmp / "tasks.csv",
                    tmp / "dependencies.csv",
                    tmp / "events.csv",
                )

if __name__ == "__main__":
    unittest.main()
