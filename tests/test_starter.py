import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from transitsafe import InputError, Query, ReleasePlanner, RequestError, Snapshot, parse_query

ROOT = Path(__file__).resolve().parents[1]
STATIONS = str(ROOT / "fixtures/stations.csv")
FARES = str(ROOT / "fixtures/fares.csv")
RIDES = str(ROOT / "fixtures/rides.csv")
QUERIES = str(ROOT / "fixtures/requests.jsonl")


class StarterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = Snapshot.load(STATIONS, FARES, RIDES)

    def test_snapshot_retries_not_double_counted(self):
        self.assertEqual(len(self.snapshot.stations), 14)
        self.assertEqual(len(self.snapshot.fares), 7)
        self.assertEqual(len(self.snapshot.rides), 36)
        self.assertEqual(len(self.snapshot.sectors), 3)

    def test_parse_valid_request(self):
        query = parse_query(Path(QUERIES).read_text().splitlines()[0], self.snapshot.sectors)
        self.assertIsInstance(query, Query)
        self.assertEqual(query.sector_id, "BAY")
        self.assertEqual(query.k, 3)

    def test_reject_boolean_as_count(self):
        line = Path(QUERIES).read_text().splitlines()[6]
        with self.assertRaises(RequestError) as caught:
            parse_query(line, self.snapshot.sectors)
        self.assertEqual((caught.exception.reason, caught.exception.request_id), ("invalid_query", "bad-k"))

    def test_unknown_sector_is_isolated(self):
        line = Path(QUERIES).read_text().splitlines()[7]
        with self.assertRaises(RequestError) as caught:
            parse_query(line, self.snapshot.sectors)
        self.assertEqual(caught.exception.reason, "unknown_sector")

    def test_conflicting_retry_rejects_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(RIDES).read_text()
            other = Path(folder) / "rides.csv"
            other.write_text(source + "T101,BAY_2,40,ADULT\n")
            with self.assertRaises(InputError):
                Snapshot.load(STATIONS, FARES, str(other))

    def test_planner_interface_is_ready(self):
        planner = ReleasePlanner(self.snapshot)
        query = parse_query(Path(QUERIES).read_text().splitlines()[0], self.snapshot.sectors)
        result = planner.plan(query)
        self.assertEqual(result["request_id"], query.request_id)
        self.assertIn("status", result)

    def test_cli_preserves_physical_line_count(self):
        result = subprocess.run([sys.executable, str(ROOT / "transitsafe.py"), "plan", "--stations", STATIONS, "--fares", FARES, "--rides", RIDES, "--queries", QUERIES], capture_output=True, text=True, check=True)
        lines = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[6]["reason"], "invalid_query")
        self.assertEqual(lines[7]["reason"], "unknown_sector")
        self.assertEqual(lines[9]["request_id"], None)


if __name__ == "__main__":
    unittest.main()
