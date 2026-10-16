import tempfile
import unittest
from pathlib import Path

from netops.catalog import SnapshotError, load_snapshot
from netops.queries import QueryError, parse_query


ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    def test_fixture_is_loadable_and_replays_do_not_duplicate(self):
        snap = load_snapshot(ROOT / "fixtures/sites.csv", ROOT / "fixtures/spans.csv")
        self.assertEqual(len(snap.sites), 16)
        self.assertEqual(len(snap.spans), 19)
        self.assertFalse(snap.spans["S-18"].enabled)

    def test_conflicting_span_replay_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            spans = Path(folder) / "spans.csv"
            spans.write_text("span_id,site_a,site_b,enabled\nS-06,X-3,A-2,true\nS-06,X-3,A-2,false\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(ROOT / "fixtures/sites.csv", spans)

    def test_missing_core_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            sites = Path(folder) / "sites.csv"
            sites.write_text("site_id,kind,active_accounts,priority_accounts\nA,access,2,1\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(sites, ROOT / "fixtures/spans.csv")

    def test_query_shapes_and_boolean_limit(self):
        self.assertEqual(parse_query('{"request_id":"x","type":"top","limit":2}', {"S-1"})["limit"], 2)
        with self.assertRaises(QueryError) as ctx:
            parse_query('{"request_id":"x","type":"top","limit":true}', {"S-1"})
        self.assertEqual(ctx.exception.reason, "invalid_query")

    def test_unknown_span(self):
        with self.assertRaises(QueryError) as ctx:
            parse_query('{"request_id":"x","type":"span","span_id":"missing"}', {"S-1"})
        self.assertEqual(ctx.exception.reason, "unknown_span")


if __name__ == "__main__":
    unittest.main()

