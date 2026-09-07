import tempfile
import unittest
from pathlib import Path

from migration.io import DatasetError, load_adapters, load_requests, load_schemas


ROOT = Path(__file__).resolve().parents[1]


class IoTests(unittest.TestCase):
    def test_fixture_loads_and_exact_duplicate_adapter_is_deduplicated(self):
        schemas = load_schemas(ROOT / "fixtures" / "schemas.csv")
        adapters = load_adapters(ROOT / "fixtures" / "adapters.csv", schemas)
        requests = load_requests(ROOT / "fixtures" / "requests.jsonl")

        self.assertEqual(10, len(schemas))
        self.assertEqual(18, len(adapters))
        self.assertEqual(7, len(requests))
        self.assertEqual(len({adapter.adapter_id for adapter in adapters}), len(adapters))

    def test_conflicting_adapter_id_is_rejected(self):
        schemas = load_schemas(ROOT / "fixtures" / "schemas.csv")
        content = (
            "adapter_id,from_schema,to_schema,region,latency_ms,quality_loss_ppm,cost_micros\n"
            "dup,crm-v1,crm-v2,*,1,1,1\n"
            "dup,crm-v1,crm-v2,*,2,1,1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adapters.csv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(DatasetError):
                load_adapters(path, schemas)


if __name__ == "__main__":
    unittest.main()
