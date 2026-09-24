import unittest
from pathlib import Path
from flagdesk.store import FlagStore, StaleRevision, ValidationError
ROOT=Path(__file__).resolve().parents[1]

class StoreTest(unittest.TestCase):
    def setUp(self): self.store=FlagStore(ROOT/"fixtures"/"flags.json")
    def test_list_order_and_filter(self):
        p=self.store.list_flags(status="active")
        pairs=[(f["owner"],f["key"]) for f in p["flags"]]
        self.assertEqual(pairs,sorted(pairs))
        self.assertTrue(all(f["status"]=="active" for f in p["flags"]))
    def test_owner_filter(self):
        self.assertEqual([f["key"] for f in self.store.list_flags(owner="search")["flags"]],["search-reranker"])
    def test_note_change_increments_once(self):
        before=self.store.get_flag("flag-search-reranker"); rev=self.store.dataset_revision
        p=self.store.update_note("flag-search-reranker",before["revision"],"  investigate ranking  ")
        self.assertTrue(p["changed"]);self.assertEqual(p["flag"]["operatorNote"],"investigate ranking")
        self.assertEqual(p["flag"]["revision"],before["revision"]+1);self.assertEqual(p["datasetRevision"],rev+1)
    def test_same_note_noop(self):
        before=self.store.get_flag("flag-ai-copilot");rev=self.store.dataset_revision
        p=self.store.update_note("flag-ai-copilot",before["revision"]," Pilot tenants only. ")
        self.assertFalse(p["changed"]);self.assertEqual(p["flag"]["revision"],before["revision"]);self.assertEqual(p["datasetRevision"],rev)
    def test_stale_note(self):
        before=self.store.get_flag("flag-mobile-nav")
        with self.assertRaises(StaleRevision): self.store.update_note("flag-mobile-nav",before["revision"]+1,"stale")
        self.assertEqual(self.store.get_flag("flag-mobile-nav"),before)
    def test_note_length(self):
        before=self.store.get_flag("flag-mobile-nav")
        with self.assertRaises(ValidationError): self.store.update_note("flag-mobile-nav",before["revision"],"x"*241)

if __name__=="__main__": unittest.main()
