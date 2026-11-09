"""POST-PRACTICE ONLY: run with python3 -m unittest discover -s evaluator -v.
These tests should FAIL against the intentionally unfinished candidate starter.
"""
import json
import unittest
from pathlib import Path
from transitsafe import Snapshot, ReleasePlanner, parse_query, Query

ROOT = Path(__file__).resolve().parents[1]


class EvaluatorAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = Snapshot.load(str(ROOT / "fixtures/stations.csv"), str(ROOT / "fixtures/fares.csv"), str(ROOT / "fixtures/rides.csv"))
        cls.planner = ReleasePlanner(cls.snapshot)
        cls.requests = [x for x in (ROOT / "fixtures/requests.jsonl").read_text().splitlines() if x.startswith("{")]

    def plan_line(self, line):
        return self.planner.plan(parse_query(line, self.snapshot.sectors))

    def test_dense_sector_window_optimum(self):
        output = self.plan_line(self.requests[0])
        self.assertEqual(output, {"request_id":"release-bay-morning","status":"ok","records":21,"released":17,"suppressed":4,"geo_level":0,"time_level":2,"fare_level":2,"loss":324})

    def test_zero_suppression_budget(self):
        output = self.plan_line(self.requests[1])
        self.assertEqual(output, {"request_id":"release-bay-strict","status":"ok","records":21,"released":21,"suppressed":0,"geo_level":2,"time_level":2,"fare_level":1,"loss":462})

    def test_empty_window(self):
        output = self.plan_line(self.requests[2])
        self.assertEqual(output, {"request_id":"release-quiet","status":"empty","records":0,"released":0,"suppressed":0,"geo_level":None,"time_level":None,"fare_level":None,"loss":None})

    def test_no_feasible_release(self):
        output = self.plan_line(self.requests[3])
        self.assertEqual(output, {"request_id":"release-few","status":"no_release","records":2,"released":0,"suppressed":0,"geo_level":None,"time_level":None,"fare_level":None,"loss":None})

    def test_zero_loss_tie_selection(self):
        output = self.plan_line(self.requests[4])
        self.assertEqual(output, {"request_id":"release-val","status":"ok","records":7,"released":7,"suppressed":0,"geo_level":1,"time_level":2,"fare_level":2,"loss":0})

    def test_same_request_id_different_window(self):
        output = self.plan_line(self.requests[5])
        self.assertEqual(output, {"request_id":"release-bay-morning","status":"ok","records":3,"released":3,"suppressed":0,"geo_level":1,"time_level":3,"fare_level":0,"loss":0})


if __name__ == "__main__":
    unittest.main()
