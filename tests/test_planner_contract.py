import unittest
from pathlib import Path

from migration.catalog import Catalog
from migration.io import load_adapters, load_requests, load_schemas
from migration.planner import MigrationPlanner


ROOT = Path(__file__).resolve().parents[1]


class PlannerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schemas = load_schemas(ROOT / "fixtures" / "schemas.csv")
        cls.requests = load_requests(ROOT / "fixtures" / "requests.jsonl")
        cls.planner = MigrationPlanner(Catalog(schemas, load_adapters(ROOT / "fixtures" / "adapters.csv", schemas)))

    def test_same_schema_has_zero_cost_empty_chain(self):
        result = self.planner.plan(next(request for request in self.requests if request.request_id == "req-004"))
        self.assertEqual("planned", result["status"])
        self.assertEqual([], result["adapter_ids"])
        self.assertEqual(0, result["total_cost_micros"])

    def test_unknown_schema_is_invalid(self):
        result = self.planner.plan(next(request for request in self.requests if request.request_id == "req-006"))
        self.assertEqual({"request_id": "req-006", "status": "invalid", "reason": "unknown_schema"}, result)


if __name__ == "__main__":
    unittest.main()
