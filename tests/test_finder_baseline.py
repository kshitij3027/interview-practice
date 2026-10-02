import unittest

from locator.finder import LockerFinder
from locator.model import QueryRecord


class FinderBaselineTests(unittest.TestCase):
    def test_invalid_query_record_is_emitted_without_search(self):
        finder = LockerFinder([])
        result = finder.resolve_all([QueryRecord(request_id="bad", query=None, error_reason="invalid_query")])
        self.assertEqual(result, [{"request_id": "bad", "status": "invalid", "reason": "invalid_query"}])


if __name__ == "__main__":
    unittest.main()
