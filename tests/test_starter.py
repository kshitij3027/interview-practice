import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from waterline import CatalogError, WaterLine, load_catalog, parse_query

ROOT = Path(__file__).resolve().parents[1]


class StarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.pipes = load_catalog(str(ROOT / 'fixtures/nodes.csv'), str(ROOT / 'fixtures/pipes.csv'))

    def test_fixture_counts_and_retried_rows(self):
        self.assertEqual((len(self.nodes), len(self.pipes)), (14, 17))

    def test_valid_empty_closure_is_safe_smoke_case(self):
        req, error = parse_query('{"request_id":"z","close_pipes":[]}', self.pipes)
        self.assertIsNone(error)
        self.assertEqual(WaterLine(self.nodes, self.pipes).review(req), {
            'request_id': 'z', 'status': 'ok', 'affected_meters': 0,
            'affected_demand_lps': 0, 'affected_critical': 0,
        })

    def test_duplicate_cuts_are_one_logical_closure(self):
        req, error = parse_query('{"request_id":"z","close_pipes":["PIPE-14","PIPE-14"]}', self.pipes)
        self.assertIsNone(error)
        self.assertEqual(req['close_pipes'], ['PIPE-14'])

    def test_unknown_link_is_isolated(self):
        req, error = parse_query('{"request_id":"z","close_pipes":["nope"]}', self.pipes)
        self.assertIsNone(req)
        self.assertEqual(error['reason'], 'unknown_pipe')

    def test_conflicting_catalog_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'pipes.csv'
            p.write_text((ROOT / 'fixtures/pipes.csv').read_text() + 'PIPE-01,J-05,J-03\n')
            with self.assertRaises(CatalogError):
                load_catalog(str(ROOT / 'fixtures/nodes.csv'), str(p))

    def test_cli_validation(self):
        result = subprocess.run([sys.executable, str(ROOT / 'waterline.py'), '--validate-only'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'nodes': 14, 'pipes': 17})

    def test_cli_emits_one_line_per_request(self):
        result = subprocess.run([sys.executable, str(ROOT / 'waterline.py')], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), len((ROOT / 'fixtures/requests.jsonl').read_text().splitlines()))
        outputs = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(outputs[8]['reason'], 'unknown_pipe')
        self.assertEqual(outputs[9]['reason'], 'invalid_query')
        self.assertEqual(outputs[11]['reason'], 'invalid_query')


if __name__ == '__main__':
    unittest.main()
