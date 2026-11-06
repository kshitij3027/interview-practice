import tempfile
import unittest
from pathlib import Path
from pulserank.input import SnapshotError, load_snapshot, parse_query
from pulserank.models import Query


ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_snapshot(ROOT / "fixtures/scopes.csv", ROOT / "fixtures/observations.csv")

    def test_revisions_are_selected_by_number_not_row_order(self):
        snapshot = self.snapshot
        self.assertEqual(snapshot.latest["req-g2"].revision, 3)
        self.assertEqual(snapshot.latest["req-g2"].latency_us, 60000)
        self.assertEqual(snapshot.latest["req-g4"].op, "cancel")
        self.assertEqual(snapshot.latest["req-g1"].region, "eu-central")

    def test_replays_do_not_create_new_logical_requests(self):
        self.assertEqual(self.snapshot.rows_seen, 25)
        self.assertEqual(len(self.snapshot.scopes), 8)
        self.assertEqual(len(self.snapshot.latest), 18)
        self.assertEqual(len(self.snapshot.live), 16)

    def test_conflicting_replay_rejects_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            scopes = Path(tmp) / "scopes.csv"
            rows = Path(tmp) / "rows.csv"
            scopes.write_text("service_id,region,budget_us\ngateway,us,50\n")
            rows.write_text("request_id,revision,op,service_id,region,at_ms,latency_us\n"
                            "a,1,upsert,gateway,us,1,2\na,1,upsert,gateway,us,1,3\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(scopes, rows)

    def test_invalid_superseded_row_rejects_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            scopes = Path(tmp) / "scopes.csv"
            rows = Path(tmp) / "rows.csv"
            scopes.write_text("service_id,region,budget_us\ngateway,us,50\n")
            rows.write_text("request_id,revision,op,service_id,region,at_ms,latency_us\n"
                            "a,2,upsert,gateway,us,1,2\na,1,upsert,gateway,us,00,3\n")
            with self.assertRaises(SnapshotError):
                load_snapshot(scopes, rows)

    def test_valid_and_invalid_queries_remain_independent(self):
        scopes = self.snapshot.scopes
        valid = parse_query('{"query_id":"one","service_id":"gateway","region":"us-west","from_ms":0,"until_ms":1}', scopes)
        self.assertIsInstance(valid, Query)
        self.assertEqual(parse_query('{"query_id":"one","service_id":"gateway","region":"us-west","from_ms":true,"until_ms":1}', scopes)["reason"], "invalid_query")
        self.assertEqual(parse_query('{"query_id":"one","service_id":"gateway","region":"nowhere","from_ms":0,"until_ms":1}', scopes)["reason"], "unknown_scope")
        self.assertIsNone(parse_query("broken", scopes)["query_id"])
