import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from coverguard import CoverageAudit, load_snapshot, parse_audit

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'fixtures'


class StarterTests(unittest.TestCase):
    def test_snapshot_loads_and_resolves_latest_revisions(self):
        snapshot = load_snapshot(FIX/'scopes.csv', FIX/'probes.csv', FIX/'observations.csv')
        self.assertEqual(len(snapshot.scopes), 4)
        self.assertEqual(len(snapshot.probes), 11)
        self.assertEqual(snapshot.active['E001'], ('EA1', 0, 10))
        self.assertNotIn('E011', snapshot.active)
        self.assertNotIn('W005', snapshot.active)
        self.assertEqual(snapshot.active['C004'], ('CB3', 125, 135))

    def test_query_validation(self):
        valid, error = parse_audit('{"audit_id":"q","scope_id":"EAST","from_ms":0,"until_ms":4,"min_vendors":2}')
        self.assertIsNone(error)
        self.assertEqual(valid['min_vendors'], 2)
        for body in ('', '[]', 'not JSON', '{"audit_id":"q","scope_id":"EAST","from_ms":0,"until_ms":4,"min_vendors":true}',
                     '{"audit_id":"q","scope_id":"EAST","from_ms":4,"until_ms":4,"min_vendors":2}'):
            self.assertEqual(parse_audit(body)[1]['reason'], 'invalid_audit')
        self.assertEqual(parse_audit('{"audit_id":"q","scope_id":"EAST","from_ms":4,"until_ms":4,"min_vendors":2}')[1]['audit_id'], 'q')

    def test_implementation_is_candidate_owned(self):
        snapshot = load_snapshot(FIX/'scopes.csv', FIX/'probes.csv', FIX/'observations.csv')
        result = CoverageAudit(snapshot).evaluate({'audit_id': 'q', 'scope_id': 'EAST', 'from_ms': 0, 'until_ms': 10, 'min_vendors': 2})
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('audit_id'), 'q')
        self.assertIn(result.get('status'), ('unimplemented', 'ok'))

    def test_catalog_conflict_fails_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory)/'observations.csv'
            filename.write_text((FIX/'observations.csv').read_text() + 'E001,2,upsert,EA1,0,11\n', encoding='utf-8')
            process = subprocess.run([sys.executable, '-B', str(ROOT/'coverguard.py'),
                                      '--scopes',str(FIX/'scopes.csv'),'--probes',str(FIX/'probes.csv'),
                                      '--observations',str(filename),'--audits',str(FIX/'audits.jsonl')],
                                     capture_output=True,text=True,cwd=ROOT)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(process.stdout, '')
            self.assertIn('catalog error', process.stderr)

    def test_cli_is_wired(self):
        process = subprocess.run([sys.executable, '-B','coverguard.py'], capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(process.stdout.splitlines()), 23)
        records = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(records[12]['reason'], 'unknown_scope')
        self.assertEqual(records[13]['reason'], 'invalid_audit')
        self.assertIn(records[0]['status'], ('unimplemented', 'ok'))


if __name__ == '__main__':
    unittest.main()
