import tempfile
import unittest
from pathlib import Path

from resolver import load_requests, load_rules, parse_utc_timestamp, result_for


class BaselineTests(unittest.TestCase):
    def test_fixture_rules_parse_and_deduplicate(self):
        rules = load_rules("fixtures/rules.csv")
        self.assertEqual(len(rules), 10)
        self.assertEqual(len({r.rule_id for r in rules}), 10)

    def test_fixture_requests_parse(self):
        requests = list(load_requests("fixtures/requests.jsonl"))
        self.assertEqual(len(requests), 8)
        self.assertEqual(requests[0].request_id, "req-001")

    def test_timestamp_requires_utc(self):
        with self.assertRaises(ValueError):
            parse_utc_timestamp("2026-08-15T12:00:00")

    def test_conflicting_duplicate_rule_id_fails(self):
        content = """rule_id,tenant,region,path_pattern,valid_from,valid_to,priority,action,destination
x,*,*,**,2026-01-01T00:00:00Z,,1,route,a
x,*,*,**,2026-01-01T00:00:00Z,,2,route,b
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.csv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicting rows"):
                load_rules(path)

    def test_result_shape_without_match(self):
        request = next(iter(load_requests("fixtures/requests.jsonl")))
        out = result_for(request, None)
        self.assertEqual(out["matched_rule_id"], None)
        self.assertEqual(out["action"], "default")


if __name__ == "__main__":
    unittest.main()
