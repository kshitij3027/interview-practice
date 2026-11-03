import unittest
from app.store import LotStore, StoreError


class LotStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = LotStore()

    def test_list_sorted_and_total_before_limit(self):
        result = self.store.list_lots(limit=3)
        self.assertEqual(result['total'], 12)
        self.assertEqual([r['id'] for r in result['lots']], ['LOT-1001', 'LOT-1002', 'LOT-1003'])

    def test_search_and_filters(self):
        self.assertEqual(self.store.list_lots(plant='P-N', status='closed')['total'], 0)
        self.assertEqual(self.store.list_lots(q='Rush')['lots'][0]['id'], 'LOT-1003')

    def test_detail_includes_samples_and_spec(self):
        detail = self.store.detail('LOT-1001')
        self.assertEqual(detail['specification']['minSamples'], 2)
        self.assertEqual(detail['samples'][0]['sampleId'], 'S-OLD')

    def test_notes_change_revisions_once(self):
        original = self.store.detail('LOT-1001')['lot']
        res = self.store.edit_note('LOT-1001', '  inspected  ', original['revision'])
        self.assertEqual(res['lot']['note'], 'inspected')
        self.assertEqual(res['lot']['revision'], original['revision'] + 1)
        self.assertEqual(res['datasetRevision'], 2)
        no_op = self.store.edit_note('LOT-1001', ' inspected ', res['lot']['revision'])
        self.assertEqual(no_op['datasetRevision'], 2)

    def test_stale_note_not_mutated(self):
        with self.assertRaises(StoreError) as cm:
            self.store.edit_note('LOT-1001', 'bad', 0)
        self.assertEqual(cm.exception.status, 409)
        self.assertEqual(self.store.detail('LOT-1001')['lot']['note'], 'Awaiting morning QC run.')

    def test_external_mutations_cannot_change_store(self):
        detail = self.store.detail('LOT-1001')
        detail['lot']['note'] = 'mutated'
        detail['samples'].clear()
        self.assertEqual(self.store.detail('LOT-1001')['lot']['note'], 'Awaiting morning QC run.')
        self.assertEqual(len(self.store.detail('LOT-1001')['samples']), 1)

    def test_reject_invalid_inputs(self):
        for args in [{'limit':0}, {'status':'RELEASED'}, {'plant':'P-404'}]:
            with self.assertRaises(StoreError): self.store.list_lots(**args)
        with self.assertRaises(StoreError): self.store.edit_note('LOT-1001', 22, 1)


if __name__ == '__main__': unittest.main()
