import csv
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from costcanopy import CatalogError, Center, inspect_operations, load_centers

ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    def make_catalog(self, lines):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False) as file:
            file.write("center_id,parent_id,budget_cents\n" + "\n".join(lines) + "\n")
            name = file.name
        self.addCleanup(lambda: os.unlink(name))
        return name

    def test_fixture_loads(self):
        catalog = load_centers(ROOT / "fixtures/centers.csv")
        self.assertEqual(len(catalog), 16)
        self.assertEqual(catalog["ZERO"], Center("ZERO", "ALPHA-FIELD", 0))

    def test_replayed_identical_row(self):
        filename = self.make_catalog(["A,,0", "B,A,5", "B,A,5"])
        self.assertEqual(len(load_centers(filename)), 2)

    def test_conflicting_definition_rejected(self):
        filename = self.make_catalog(["A,,0", "A,,1"])
        with self.assertRaises(CatalogError):
            load_centers(filename)

    def test_unknown_parent_rejected(self):
        filename = self.make_catalog(["A,B,5"])
        with self.assertRaises(CatalogError):
            load_centers(filename)

    def test_cycles_rejected(self):
        filename = self.make_catalog(["A,B,1", "B,C,1", "C,A,1"])
        with self.assertRaises(CatalogError):
            load_centers(filename)

    def test_deep_chain_does_not_recurse(self):
        filename = self.make_catalog(["C0,,0"] + [f"C{i},C{i-1},1" for i in range(1, 4000)])
        self.assertEqual(len(load_centers(filename)), 4000)

    def test_boolean_or_negative_budget_rejected(self):
        for bad in ["yes", "-1", "00", "1000000000001"]:
            with self.subTest(bad=bad):
                with self.assertRaises(CatalogError):
                    load_centers(self.make_catalog([f"A,,{bad}"]))

    def test_cli_check_fixture(self):
        result = subprocess.run([sys.executable, str(ROOT / "costcanopy.py"), "check", "--centers", str(ROOT / "fixtures/centers.csv"), "--operations", str(ROOT / "fixtures/operations.jsonl")], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("centers=16", result.stdout)
        self.assertIn("malformed_json=1", result.stdout)


if __name__ == "__main__":
    unittest.main()
