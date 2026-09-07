import unittest
from pathlib import Path

from migration.catalog import Catalog
from migration.io import load_adapters, load_schemas


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schemas = load_schemas(ROOT / "fixtures" / "schemas.csv")
        cls.catalog = Catalog(schemas, load_adapters(ROOT / "fixtures" / "adapters.csv", schemas))

    def test_region_and_disabled_filters_compose(self):
        us_ids = {
            adapter.adapter_id
            for adapter in self.catalog.eligible_outgoing("bridge-b", "us", frozenset({"a-04"}))
        }
        eu_ids = {
            adapter.adapter_id
            for adapter in self.catalog.eligible_outgoing("bridge-b", "eu", frozenset())
        }
        self.assertEqual({"a-05", "a-11"}, us_ids)
        self.assertEqual({"a-04", "a-11"}, eu_ids)

    def test_outgoing_is_deterministic(self):
        ids = [adapter.adapter_id for adapter in self.catalog.outgoing["crm-v1"]]
        self.assertEqual(sorted(ids), ids)


if __name__ == "__main__":
    unittest.main()
