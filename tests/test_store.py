import unittest
from pathlib import Path

from permitlens.store import DomainError, VisitStore

BASE = Path(__file__).resolve().parents[1]


class VisitStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = VisitStore(BASE / 'fixtures/workspace.json', BASE / 'fixtures/credentials.jsonl')

    def test_list_filters_and_stable_order(self):
        result = self.store.list_visits('harbor', status='requested')
        self.assertEqual(result['total'], 5)
        ids = [v['id'] for v in result['items']]
        self.assertEqual(ids, ['VIS-001', 'VIS-002', 'VIS-003', 'VIS-004', 'VIS-005'])
        self.assertEqual(self.store.list_visits('harbor', query='brightSPARK')['total'], 3)

    def test_tenant_isolation(self):
        self.assertEqual(self.store.list_visits('orchid')['total'], 2)
        with self.assertRaises(DomainError) as ctx:
            self.store.get_visit('harbor', 'VIS-009')
        self.assertEqual(ctx.exception.status, 404)

    def test_detail_joins_and_returns_copies(self):
        detail = self.store.get_visit('harbor', 'VIS-001')
        self.assertEqual(detail['visit']['siteName'], 'Harbor Assembly Yard')
        detail['visit']['note'] = 'mutated'
        self.assertEqual(self.store.get_visit('harbor', 'VIS-001')['visit']['note'], 'Bring authorized PPE.')

    def test_note_edit_trim_and_exact_revision_accounting(self):
        original = self.store.get_visit('harbor', 'VIS-001')
        version = original['visit']['revision']
        base = self.store.dataset_revision
        modified = self.store.update_note('harbor', 'VIS-001', {'note': '  Supervisor called  ', 'expectedRevision': version})
        self.assertEqual(modified['visit']['note'], 'Supervisor called')
        self.assertEqual(modified['visit']['revision'], version + 1)
        self.assertEqual(modified['datasetRevision'], base + 1)
        unchanged = self.store.update_note('harbor', 'VIS-001', {'note': 'Supervisor called', 'expectedRevision': version + 1})
        self.assertEqual(unchanged['datasetRevision'], base + 1)

    def test_stale_note_does_not_mutate(self):
        version = self.store.get_visit('harbor', 'VIS-002')['visit']['revision']
        self.store.update_note('harbor', 'VIS-002', {'note': 'first', 'expectedRevision': version})
        current = self.store.dataset_revision
        with self.assertRaises(DomainError) as ctx:
            self.store.update_note('harbor', 'VIS-002', {'note': 'second', 'expectedRevision': version})
        self.assertEqual(ctx.exception.code, 'stale_revision')
        self.assertEqual(self.store.dataset_revision, current)

    def test_note_validation(self):
        version = self.store.get_visit('harbor', 'VIS-001')['visit']['revision']
        for body in ({'note': 'x', 'expectedRevision': True}, {'note': 1, 'expectedRevision': version}, {'note': 'y', 'expectedRevision': version, 'extra': 1}):
            with self.subTest(body=body), self.assertRaises(DomainError) as ctx:
                self.store.update_note('harbor', 'VIS-001', body)
            self.assertEqual(ctx.exception.status, 400)


if __name__ == '__main__':
    unittest.main()
