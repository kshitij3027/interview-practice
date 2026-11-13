"""POST-PRACTICE ONLY: evaluator acceptance checks, not part of the green starter tests."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FixtureAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = subprocess.run([sys.executable, str(ROOT / 'waterline.py')], cwd=ROOT, text=True, capture_output=True)
        if p.returncode:
            raise RuntimeError(p.stderr)
        cls.output = [json.loads(row) for row in p.stdout.splitlines()]

    def test_branch_cut(self):
        self.assertEqual(self.output[1], {'request_id': 'single_branch', 'status': 'ok', 'affected_meters': 505, 'affected_demand_lps': 280, 'affected_critical': 6})

    def test_two_source_isolation(self):
        self.assertEqual((self.output[2]['affected_meters'], self.output[2]['affected_demand_lps'], self.output[2]['affected_critical']), (2040, 1090, 10))

    def test_parallel_distinction(self):
        self.assertEqual(self.output[3]['affected_meters'], 0)
        self.assertEqual((self.output[4]['affected_meters'], self.output[4]['affected_demand_lps'], self.output[4]['affected_critical']), (245, 145, 3))

    def test_duplicate_close_is_idempotent(self):
        self.assertEqual((self.output[5]['affected_meters'], self.output[5]['affected_demand_lps'], self.output[5]['affected_critical']), (45, 35, 1))

    def test_isolated_legacy_zone_not_counted(self):
        self.assertEqual(self.output[6]['affected_meters'], 0)
        self.assertEqual(self.output[7]['affected_meters'], 0)

    def test_invalid_lines_and_later_query(self):
        self.assertEqual([self.output[i]['reason'] for i in (8,9,10,11)], ['unknown_pipe', 'invalid_query', 'invalid_query', 'invalid_query'])
        self.assertEqual(self.output[12]['affected_meters'], 505)


if __name__ == '__main__':
    unittest.main()
