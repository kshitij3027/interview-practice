import unittest
from server.store import WorkOrders, StoreError

class DirectoryTests(unittest.TestCase):
    def setUp(self):
        self.store = WorkOrders()

    def test_catalog_has_two_accounts(self):
        self.assertEqual(len(self.store.catalog()["accounts"]), 2)

    def test_list_filters_and_stable_order(self):
        result = self.store.list_jobs("acme", status="in_progress", limit=2)
        self.assertEqual(result["total"], 2)
        self.assertEqual([j["id"] for j in result["jobs"]], ["WO-101", "WO-104"])

    def test_search_case_insensitive(self):
        result = self.store.list_jobs("acme", search="COMPRESSOR")
        self.assertEqual([j["id"] for j in result["jobs"]], ["WO-101", "WO-105"])

    def test_ownership_is_enforced(self):
        with self.assertRaises(StoreError) as ctx:
            self.store.detail("acme", "WO-202")
        self.assertEqual(ctx.exception.status, 404)

    def test_note_change_increments_once(self):
        before = self.store.detail("acme", "WO-101")["job"]
        result = self.store.note("acme", "WO-101", "  New note  ", before["revision"])
        self.assertEqual(result["job"]["revision"], before["revision"] + 1)
        self.assertEqual(result["job"]["note"], "New note")
        self.assertEqual(result["datasetRevision"], 8)
        again = self.store.note("acme", "WO-101", "New note", result["job"]["revision"])
        self.assertTrue(again["unchanged"])
        self.assertEqual(again["datasetRevision"], 8)

    def test_stale_note_rejected(self):
        before = self.store.detail("acme", "WO-102")["job"]
        self.store.note("acme", "WO-102", "changed", before["revision"])
        with self.assertRaises(StoreError) as ctx:
            self.store.note("acme", "WO-102", "oops", before["revision"])
        self.assertEqual(ctx.exception.code, "STALE_REVISION")

    def test_reject_bad_limit_data_is_not_modified(self):
        before = self.store.dataset_revision
        with self.assertRaises(StoreError):
            self.store.note("acme", "WO-101", 22, 1)
        self.assertEqual(self.store.dataset_revision, before)
