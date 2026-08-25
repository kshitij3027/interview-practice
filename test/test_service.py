import unittest
from src.service import CaseService
from src.store import CaseStore

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = CaseService(CaseStore())

    def test_filters_by_status_and_priority(self):
        cases = self.service.list_cases(status="open", priority="urgent")
        self.assertEqual([c["id"] for c in cases], ["c-103"])

    def test_rejects_invalid_filter(self):
        with self.assertRaisesRegex(ValueError, "invalid_status"):
            self.service.list_cases(status="closed")

    def test_requires_integer_revision_for_note(self):
        with self.assertRaisesRegex(ValueError, "invalid_revision"):
            self.service.add_note("c-101", "x", "2")

if __name__ == "__main__": unittest.main()
