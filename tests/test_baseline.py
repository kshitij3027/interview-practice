import tempfile
import unittest
from pathlib import Path

from claimsignal.data import Case, iter_case_requests, load_rules, parse_case_record


class BaselineTests(unittest.TestCase):
    def test_catalog_baseline(self):
        rules = load_rules('fixtures/rules.csv')
        self.assertEqual(19, len(rules))
        self.assertEqual('R01', rules[0].rule_id)

    def test_valid_case_parsing(self):
        case = parse_case_record({'case_id': 'c1', 'channel': 'chat', 'text': 'Hi!', 'max_findings': 2})
        self.assertEqual(Case('c1', 'chat', 'Hi!', 2), case)

    def test_bool_is_not_integer(self):
        with self.assertRaises(ValueError):
            parse_case_record({'case_id': 'c1', 'channel': 'chat', 'text': 'Hi', 'max_findings': True})

    def test_replay_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'rules.csv'
            path.write_text('rule_id,issue_code,phrase,weight,channels,active\nX,WATER,leak,5,*,true\nX,WATER,leak,6,*,true\n')
            with self.assertRaisesRegex(ValueError, 'conflicting rule replay'):
                load_rules(path)

    def test_bad_lines_do_not_end_stream(self):
        stream = list(iter_case_requests('fixtures/cases.jsonl'))
        self.assertEqual(13, len(stream))
        self.assertEqual(3, sum(case is None for case, _ in stream))
        self.assertEqual('C12', stream[-1][0].case_id)

    def test_service_accepts_loaded_catalog(self):
        from claimsignal.service import ClaimResolver
        resolver = ClaimResolver(load_rules('fixtures/rules.csv'))
        self.assertEqual(19, len(resolver.rules))


if __name__ == '__main__':
    unittest.main()
