"""Foundation checks, not customer feature acceptance tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from batchpath.catalog import CatalogError, load_catalog
from batchpath.engine import BatchPath
from batchpath.requests import Query, parse_query

ROOT = Path(__file__).resolve().parents[1]


class StarterChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / "fixtures/datasets.csv", ROOT / "fixtures/links.csv")

    def test_catalog_dimensions(self):
        self.assertEqual(len(self.catalog.datasets), 14)
        self.assertEqual(len(self.catalog.active_links), 12)
        self.assertEqual(self.catalog.tenants, {"ACME", "BLUE"})

    def test_latest_retraction(self):
        self.assertNotIn("A5", {x.link_id for x in self.catalog.active_links})

    def test_latest_correction(self):
        self.assertEqual(next(x.prerequisite_id for x in self.catalog.active_links if x.link_id == "A6"), "RAW_B")

    def test_valid_request_parsing(self):
        query, error = parse_query('{"request_id":"x","tenant_id":"ACME","target_id":"MART","deadline_min":10}')
        self.assertEqual(query, Query("x", "ACME", "MART", 10))
        self.assertIsNone(error)

    def test_invalid_type_preserves_valid_id(self):
        query, error = parse_query('{"request_id":"x","tenant_id":"ACME","target_id":"MART","deadline_min":true}')
        self.assertIsNone(query)
        self.assertEqual(error, {"request_id": "x", "status": "invalid", "reason": "invalid_query"})

    def test_empty_physical_line(self):
        self.assertEqual(parse_query("\n")[1]["reason"], "invalid_query")

    def test_conflicting_dataset_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "datasets.csv"
            p.write_text((ROOT / "fixtures/datasets.csv").read_text() + "RAW_A,ACME,9,2\n")
            with self.assertRaises(CatalogError):
                load_catalog(p, ROOT / "fixtures/links.csv")

    def test_conflicting_revision_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "links.csv"
            p.write_text((ROOT / "fixtures/links.csv").read_text() + "A1,1,upsert,ACME,RAW_B,CLEAN,2\n")
            with self.assertRaises(CatalogError):
                load_catalog(ROOT / "fixtures/datasets.csv", p)

    def test_validation_cli(self):
        run = subprocess.run([sys.executable, "batchpath.py", "validate", "--datasets", "fixtures/datasets.csv", "--links", "fixtures/links.csv"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn('"datasets":14', run.stdout)
        self.assertEqual(run.stderr, "")

    def test_engine_interface(self):
        self.assertTrue(callable(BatchPath(self.catalog).assess))


if __name__ == "__main__":
    unittest.main()
