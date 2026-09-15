import unittest
from pathlib import Path

from app.store import CampaignStore, ConflictError, ValidationError

ROOT = Path(__file__).resolve().parents[1]


class CampaignStoreTest(unittest.TestCase):
    def setUp(self):
        self.store = CampaignStore(ROOT / "fixtures")

    def test_fixture_loading(self):
        self.assertEqual(4, len(self.store.campaigns))
        self.assertEqual(7, len(self.store.budget_changes))
        self.assertGreaterEqual(len(self.store.spend_events), 10)

    def test_list_sorted_and_filtered(self):
        all_rows = self.store.list_campaigns()
        self.assertEqual(["cmp-atlas", "cmp-boreal", "cmp-cirrus", "cmp-delta"], [r["id"] for r in all_rows])
        paused = self.store.list_campaigns("paused")
        self.assertEqual(["cmp-boreal"], [r["id"] for r in paused])

    def test_status_change_increments_revisions_once(self):
        before = self.store.get_campaign("cmp-atlas")
        updated = self.store.set_status("cmp-atlas", "paused", before["revision"])
        self.assertEqual("paused", updated["status"])
        self.assertEqual(before["revision"] + 1, updated["revision"])
        self.assertEqual(before["dataset_revision"] + 1, updated["dataset_revision"])

    def test_noop_status_change_does_not_increment(self):
        before = self.store.get_campaign("cmp-atlas")
        updated = self.store.set_status("cmp-atlas", "active", before["revision"])
        self.assertEqual(before["revision"], updated["revision"])
        self.assertEqual(before["dataset_revision"], updated["dataset_revision"])

    def test_stale_status_write_does_not_mutate(self):
        before = self.store.get_campaign("cmp-atlas")
        with self.assertRaises(ConflictError):
            self.store.set_status("cmp-atlas", "paused", before["revision"] - 1)
        after = self.store.get_campaign("cmp-atlas")
        self.assertEqual(before, after)

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.store.set_status("cmp-atlas", "archived", 3)


if __name__ == "__main__":
    unittest.main()
