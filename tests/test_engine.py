import unittest
from pathlib import Path
from pulserank.engine import LatencyAudit
from pulserank.input import load_snapshot
from pulserank.models import Query

ROOT = Path(__file__).resolve().parents[1]


class EngineContractTests(unittest.TestCase):
    def test_engine_accepts_request_and_returns_json_ready_record(self):
        snapshot = load_snapshot(ROOT / "fixtures/scopes.csv", ROOT / "fixtures/observations.csv")
        result = LatencyAudit(snapshot).assess(Query("sample", "gateway", "us-west", 0, 100))
        self.assertIsInstance(result, dict)
        self.assertEqual(result["query_id"], "sample")
        self.assertIn("status", result)
