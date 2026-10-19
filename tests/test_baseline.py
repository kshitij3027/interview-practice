"""Starter checks cover infrastructure, not the requested SLA computation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from slaops.data import SnapshotError, canonical, instant, load_snapshot
from slaops.requests import QueryError, parse_request

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "fixtures" / name for name in ("coverage.csv", "blackouts.csv", "tickets.csv", "pauses.csv")]


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_snapshot(*FILES)

    def test_catalog_loads_and_replays_deduplicate(self):
        self.assertEqual((len(self.data.coverage), len(self.data.blackouts), len(self.data.tickets), len(self.data.pauses)), (11, 6, 8, 7))

    def test_timezone_equivalence(self):
        self.assertEqual(instant("2026-10-19T08:00:00Z"), instant("2026-10-19T10:00:00+02:00"))
        self.assertEqual(canonical(instant("2026-10-19T10:00:00+02:00")), "2026-10-19T08:00:00Z")

    def test_reject_naive_timestamp(self):
        with self.assertRaises(ValueError):
            instant("2026-10-19T08:00:00")

    def test_snapshot_rejects_conflicting_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            original = FILES[0].read_text()
            path = Path(directory) / "coverage.csv"
            path.write_text(original + "W01,US-PAC,2026-10-19T07:00:00Z,2026-10-19T12:00:00Z\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(path, *FILES[1:])

    def test_query_validation(self):
        request = parse_request(json.dumps({"request_id": "ok", "type": "ticket", "ticket_id": "K-100", "as_of": "2026-10-19T10:00:00Z"}), set(self.data.tickets))
        self.assertEqual(request["ticket_id"], "K-100")
        with self.assertRaises(QueryError) as failure:
            parse_request('{"request_id":"bad","type":"overdue","as_of":"2026-10-19T10:00:00Z","limit":true}', set(self.data.tickets))
        self.assertEqual(failure.exception.request_id, "bad")

    def test_unknown_ticket_is_query_error(self):
        with self.assertRaises(QueryError) as failure:
            parse_request('{"request_id":"missing","type":"ticket","ticket_id":"K-999","as_of":"2026-10-19T10:00:00Z"}', set(self.data.tickets))
        self.assertEqual(failure.exception.reason, "unknown_ticket")

    def test_check_command(self):
        cmd = [sys.executable, str(ROOT / "promise_clock.py"), "check", "--coverage", str(FILES[0]), "--blackouts", str(FILES[1]), "--tickets", str(FILES[2]), "--pauses", str(FILES[3])]
        run = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(run.stdout)["tickets"], 8)


if __name__ == "__main__":
    unittest.main()

