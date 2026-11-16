"""Starter contract checks; feature correctness is for the candidate to establish."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from chronocheck import ChronoCheck, load_snapshot, parse_request

ROOT = Path(__file__).resolve().parents[1]
CLOCKS = ROOT / "fixtures/clocks.csv"
MEASUREMENTS = ROOT / "fixtures/measurements.csv"


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clocks, cls.active = load_snapshot(CLOCKS, MEASUREMENTS)

    def test_catalog_replay_and_revision_selection(self):
        self.assertEqual(len(self.clocks), 12)
        self.assertEqual(self.active["m_B"], ("upsert", "Acme", "edge_2", "edge_3", -20))
        self.assertNotIn("m_C", self.active)
        self.assertNotIn("m_T", self.active)

    def test_negative_calibration_and_self_calibration_survive_loading(self):
        self.assertEqual(self.active["m_E"][-1], -700)
        self.assertEqual(self.active["m_Y"][-1], 3)

    def test_request_validation_and_duplicate_ids(self):
        line = '{"request_id":"same","tenant_id":"Umbra","source_clock":"u_a","target_clock":"u_b"}'
        query, error = parse_request(line, self.clocks)
        self.assertIsNone(error)
        self.assertEqual(query, ("same", "Umbra", "u_a", "u_b"))
        self.assertIsNone(parse_request(line, self.clocks)[1])

    def test_unknown_clock_is_isolated(self):
        query, error = parse_request('{"request_id":"bad","tenant_id":"Acme","source_clock":"edge_1","target_clock":"u_a"}', self.clocks)
        self.assertIsNone(query)
        self.assertEqual(error["reason"], "unknown_clock")

    def test_bad_json_and_boolean_request_id(self):
        self.assertEqual(parse_request('{', self.clocks)[1]["reason"], "invalid_query")
        self.assertIsNone(parse_request('{"request_id":true}', self.clocks)[1]["request_id"])

    def test_conflicting_catalog_fails_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "measurements.csv"
            file.write_text(MEASUREMENTS.read_text() + "m_B,3,upsert,Acme,edge_2,edge_3,90\n")
            with self.assertRaises(ValueError):
                load_snapshot(CLOCKS, file)

    def test_cli_smoke(self):
        command = [sys.executable, str(ROOT / "chronocheck.py"), "audit", "--clocks", str(CLOCKS), "--measurements", str(MEASUREMENTS), "--requests", str(ROOT / "fixtures/requests.jsonl")]
        proc = subprocess.run(command, capture_output=True, text=True, check=True)
        answers = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(answers), 13)
        self.assertEqual(answers[0]["status"], "not_implemented")
        self.assertEqual(answers[7]["reason"], "unknown_clock")
        self.assertEqual(answers[-2]["reason"], "invalid_query")


if __name__ == "__main__":
    unittest.main()
