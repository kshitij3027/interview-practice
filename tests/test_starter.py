import io
import json
import tempfile
import unittest
from pathlib import Path

from relay import RelayPlanner, SnapshotError, load_snapshot, parse_request, run


ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hubs, cls.services = load_snapshot(ROOT / "fixtures/hubs.csv", ROOT / "fixtures/services.csv")

    def test_fixture_loads_and_exact_service_replay_collapses(self):
        self.assertGreaterEqual(len(self.hubs), 6)
        self.assertEqual(len(self.services), len(set(self.services)))
        self.assertIn("LAB-N", self.hubs)

    def test_request_parses(self):
        request = parse_request({"request_id": "Q", "origin": "LAB-N", "destination": "HOSP-S", "ready_min": 30,
                                 "deadline_min": 180, "max_legs": 4, "requires_cold": True}, self.hubs)
        self.assertEqual(request.max_legs, 4)

    def test_boolean_not_accepted_for_numeric_field(self):
        with self.assertRaises(ValueError):
            parse_request({"request_id": "Q", "origin": "LAB-N", "destination": "HOSP-S", "ready_min": True,
                           "deadline_min": 180, "max_legs": 4, "requires_cold": True}, self.hubs)

    def test_conflicting_catalog_identifier_fails_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            hubs = Path(tmp) / "hubs.csv"
            services = Path(tmp) / "services.csv"
            hubs.write_text("hub_id,transfer_min,cold_storage\nA,0,true\nA,1,true\n")
            services.write_text("service_id,from_hub,to_hub,depart_min,arrive_min,cold_enabled,slots\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(hubs, services)

    def test_invalid_request_does_not_interrupt_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            requests = Path(tmp) / "requests.jsonl"
            requests.write_text('{"request_id":"bad","origin":"ZZ","destination":"HOSP-S","ready_min":0,"deadline_min":5,"max_legs":1,"requires_cold":true}\n'
                                '{"request_id":"ok","origin":"LAB-N","destination":"HOSP-S","ready_min":0,"deadline_min":200,"max_legs":2,"requires_cold":true}\n')
            output = io.StringIO()
            run(ROOT / "fixtures/hubs.csv", ROOT / "fixtures/services.csv", requests, output)
            values = [json.loads(x) for x in output.getvalue().splitlines()]
            self.assertEqual(values[0]["status"], "invalid_request")
            self.assertEqual(values[1]["request_id"], "ok")
            self.assertIn(values[1]["status"], ("not_implemented", "ok", "unreachable"))

    def test_planner_returns_request_identifier(self):
        req = parse_request({"request_id": "Q", "origin": "LAB-N", "destination": "HOSP-S", "ready_min": 0,
                             "deadline_min": 200, "max_legs": 3, "requires_cold": True}, self.hubs)
        self.assertEqual(RelayPlanner(self.hubs, self.services).plan(req)["request_id"], "Q")


if __name__ == "__main__":
    unittest.main()
