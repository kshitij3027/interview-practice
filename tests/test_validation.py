from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readiness.loader import DatasetError, load_snapshot


class ValidationTests(unittest.TestCase):
    def _write_minimal(self, tmp: Path, dependencies: str) -> None:
        (tmp / "workflows.csv").write_text(
            "workflow_id,customer_id,name\nwf,cust,Runbook\n", encoding="utf-8"
        )
        (tmp / "tasks.csv").write_text(
            "task_id,workflow_id,priority,due_at\n"
            "a,wf,10,2026-09-28T10:00:00Z\n"
            "b,wf,20,2026-09-28T10:05:00Z\n",
            encoding="utf-8",
        )
        (tmp / "dependencies.csv").write_text(
            "task_id,prerequisite_task_id\n" + dependencies, encoding="utf-8"
        )
        (tmp / "events.csv").write_text(
            "event_id,task_id,occurred_at,version,action\n", encoding="utf-8"
        )

    def test_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write_minimal(tmp, "a,b\nb,a\n")
            with self.assertRaises(DatasetError):
                load_snapshot(
                    tmp / "workflows.csv",
                    tmp / "tasks.csv",
                    tmp / "dependencies.csv",
                    tmp / "events.csv",
                )

    def test_exact_duplicate_dependency_is_harmless(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write_minimal(tmp, "b,a\nb,a\n")
            snapshot = load_snapshot(
                tmp / "workflows.csv",
                tmp / "tasks.csv",
                tmp / "dependencies.csv",
                tmp / "events.csv",
            )
            self.assertEqual(1, len(snapshot.dependencies))


if __name__ == "__main__":
    unittest.main()
