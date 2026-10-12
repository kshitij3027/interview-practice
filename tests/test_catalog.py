import tempfile
import unittest
from pathlib import Path

from resolver.catalog import CatalogError, load_catalog, parse_request, version

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(str(FIX / "releases.csv"), str(FIX / "requirements.csv"), str(FIX / "conflicts.csv"))

    def test_numeric_versions(self):
        self.assertLess(version("2.9.9"), version("2.10.0"))
        for text in ("1.0", "01.2.3", "1.-1.0", "v1.2.3"):
            with self.assertRaises(ValueError):
                version(text)

    def test_fixture_replays_are_collapsed(self):
        self.assertIn(("agent", "2.0.0"), self.catalog.releases)
        self.assertEqual(len(self.catalog.conflicts), len(set(self.catalog.conflicts)))

    def test_invalid_request_does_not_leak_to_next(self):
        invalid, error = parse_request('{"request_id":"oops","platform":"linux-x64","max_download_kb":true,"roots":[]}')
        self.assertIsNone(invalid)
        self.assertEqual(error["request_id"], "oops")
        valid, error = parse_request('{"request_id":"ok","platform":"linux-x64","max_download_kb":10,"roots":[{"name":"agent","min_version":"1.0.0","max_version_exclusive":"3.0.0"}]}')
        self.assertIsNone(error)
        self.assertEqual(valid["request_id"], "ok")

    def test_conflicting_release_replay_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            releases = Path(directory) / "releases.csv"
            original = (FIX / "releases.csv").read_text()
            releases.write_text(original + "agent,2.0.0,linux-x64,999,true\n")
            with self.assertRaises(CatalogError):
                load_catalog(str(releases), str(FIX / "requirements.csv"), str(FIX / "conflicts.csv"))


if __name__ == "__main__":
    unittest.main()
