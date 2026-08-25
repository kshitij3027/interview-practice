import unittest
from src.store import CaseStore

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = CaseStore()

    def test_loads_cases_in_stable_order(self):
        self.assertEqual([c["id"] for c in self.store.list_cases()], ["c-101", "c-102", "c-103", "c-104"])

    def test_note_changes_only_notes_and_revision(self):
        before = self.store.get_case("c-101")
        after = self.store.add_note("c-101", "  checked logs  ", before["revision"])
        self.assertEqual(after["revision"], before["revision"] + 1)
        self.assertEqual(after["notes"][-1]["text"], "checked logs")
        for field in ["status", "priority", "owner_email", "external_version"]:
            self.assertEqual(after[field], before[field])

    def test_stale_note_does_not_mutate(self):
        before = self.store.get_case("c-102")
        with self.assertRaisesRegex(ValueError, "stale_revision"):
            self.store.add_note("c-102", "hello", before["revision"] + 1)
        self.assertEqual(self.store.get_case("c-102"), before)

if __name__ == "__main__": unittest.main()
