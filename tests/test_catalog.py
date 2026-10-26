import tempfile
import unittest
from pathlib import Path
from yardkit.data import load_snapshot, parse_query

BASE = Path(__file__).resolve().parents[1] / "fixtures"


def load():
    return load_snapshot(*(str(BASE / name) for name in ("yards.csv", "containers.csv", "links.csv", "events.csv")))


class CatalogTests(unittest.TestCase):
    def test_fixture_loads_and_deduplicates(self):
        snapshot = load()
        self.assertEqual((len(snapshot.yards), len(snapshot.containers), len(snapshot.links), len(snapshot.events)), (2, 13, 16, 30))
        self.assertEqual(snapshot.events[0].event_id, "EV-01")
        self.assertEqual(snapshot.links["L-15"].left_id, "B-01")

    def test_query_shape_and_lookup(self):
        snapshot = load()
        result = parse_query('{"request_id":"a","kind":"group","as_of_ms":3,"container_id":"B-01"}', snapshot)
        self.assertEqual(result["container_id"], "B-01")
        self.assertEqual(parse_query('{"request_id":"x","kind":"group","as_of_ms":true,"container_id":"B-01"}', snapshot)["reason"], "invalid_query")
        self.assertEqual(parse_query('{"request_id":"x","kind":"group","as_of_ms":1,"container_id":"MISSING"}', snapshot)["reason"], "unknown_container")

    def test_conflicting_replay_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.csv"
            path.write_text("event_id,occurred_ms,sequence,link_id,state\nE,1,1,L-01,open\nE,1,1,L-01,close\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicting event"):
                load_snapshot(str(BASE / "yards.csv"), str(BASE / "containers.csv"), str(BASE / "links.csv"), str(path))


if __name__ == "__main__":
    unittest.main()
