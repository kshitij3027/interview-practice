import tempfile
import unittest
from pathlib import Path
from app import store

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = store.initialize(Path(self.tmp.name) / 'test.sqlite')

    def test_catalog_and_listing(self):
        self.assertEqual(len(store.catalog()['organizations']), 3)
        results = store.list_contracts('org-cedar', path=self.db, limit=2)
        self.assertEqual(results['total'], 4)
        self.assertEqual([r['id'] for r in results['contracts']], ['ctr-101', 'ctr-102'])

    def test_search_pagination(self):
        self.assertEqual(store.list_contracts('org-cedar', q='bird', path=self.db)['contracts'][0]['id'], 'ctr-102')
        self.assertEqual(store.list_contracts('org-cedar', status='active', path=self.db)['total'], 3)
        self.assertEqual(len(store.list_contracts('org-cedar', offset=2, limit=1, path=self.db)['contracts']), 1)

    def test_org_isolation(self):
        with self.assertRaises(store.DomainError) as ctx:
            store.get_contract('ctr-105', 'org-cedar', self.db)
        self.assertEqual(ctx.exception.status, 404)

    def test_note_update_and_noop(self):
        original = store.get_contract('ctr-102', 'org-cedar', self.db)
        revised = store.edit_note('ctr-102','org-cedar',original['revision'],'  Updated  ',self.db)
        self.assertEqual(revised['note'],'Updated')
        self.assertEqual(revised['revision'],original['revision']+1)
        repeat = store.edit_note('ctr-102','org-cedar',revised['revision'],'Updated',self.db)
        self.assertEqual(repeat['revision'],revised['revision'])

    def test_stale_revision(self):
        with self.assertRaises(store.DomainError) as ctx:
            store.edit_note('ctr-102','org-cedar',999,'x',self.db)
        self.assertEqual(ctx.exception.status,409)
        self.assertEqual(ctx.exception.current['id'],'ctr-102')

    def test_invalid_input(self):
        for data in [(True,'x'), (1,8)]:
            with self.assertRaises(store.DomainError):
                store.edit_note('ctr-102','org-cedar',*data,path=self.db)
        with self.assertRaises(store.DomainError):
            store.list_contracts('org-cedar',limit=0,path=self.db)

if __name__ == '__main__': unittest.main()
