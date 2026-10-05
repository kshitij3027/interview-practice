import unittest
from pathlib import Path

from bundlelock.catalog import Catalog
from bundlelock.io import iter_request_payloads, parse_request
from bundlelock.models import Version


ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog.load(
            ROOT / "fixtures/packages.csv",
            ROOT / "fixtures/versions.csv",
            ROOT / "fixtures/dependencies.csv",
            ROOT / "fixtures/installed.csv",
        )

    def test_numeric_version_order(self):
        self.assertGreater(Version.parse("2.10.0"), Version.parse("2.9.9"))

    def test_noncanonical_versions_rejected(self):
        for raw in ("1.2", "01.2.3", "1.2.3-beta", ""):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    Version.parse(raw)

    def test_fixture_shape_and_dependency_replay(self):
        self.assertEqual((len(self.catalog.packages), len(self.catalog.releases)), (7, 17))
        self.assertEqual(self.catalog.dependency_count(), 15)
        key = ("app-shell", Version.parse("4.1.0"))
        ids = [d.dependency_id for d in self.catalog.dependencies_by_release[key]]
        self.assertEqual(ids.count("dep-shell-auth-410"), 1)

    def test_request_baseline_shape(self):
        rows = list(iter_request_payloads(ROOT / "fixtures/requests.jsonl"))
        self.assertEqual(len(rows), 5)
        valid = invalid = 0
        for _, payload, decoded in rows:
            if not decoded:
                invalid += 1
                continue
            try:
                parse_request(payload, self.catalog)
                valid += 1
            except ValueError:
                invalid += 1
        self.assertEqual((valid, invalid), (4, 1))

    def test_duplicate_blocked_versions_collapse(self):
        payload = {
            "request_id": "dup",
            "targets": [{"package_id": "auth-kit", "min_version": "2.0.0", "max_version_exclusive": "3.0.0"}],
            "blocked_versions": ["auth-kit@2.1.0", "auth-kit@2.1.0"],
            "allow_canary": False,
            "max_changes": 2,
        }
        self.assertEqual(len(parse_request(payload, self.catalog).blocked_versions), 1)

    def test_bool_is_not_max_changes(self):
        payload = {
            "request_id": "bool",
            "targets": [{"package_id": "auth-kit", "min_version": "2.0.0", "max_version_exclusive": "3.0.0"}],
            "blocked_versions": [],
            "allow_canary": False,
            "max_changes": True,
        }
        with self.assertRaises(ValueError):
            parse_request(payload, self.catalog)


if __name__ == "__main__":
    unittest.main()
