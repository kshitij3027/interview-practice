from __future__ import annotations

import unittest
from datetime import timezone

from recovery.time_utils import format_utc, parse_utc, require_aligned


class TimeUtilsTests(unittest.TestCase):
    def test_timestamp_normalizes_to_utc(self) -> None:
        parsed = parse_utc("2026-09-04T05:00:00-04:00", field="sample")
        self.assertEqual(timezone.utc, parsed.tzinfo)
        self.assertEqual("2026-09-04T09:00:00Z", format_utc(parsed))

    def test_timezone_less_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_utc("2026-09-04T09:00:00", field="sample")

    def test_alignment_is_enforced(self) -> None:
        parsed = parse_utc("2026-09-04T09:07:00Z", field="sample")
        with self.assertRaisesRegex(ValueError, "15-minute"):
            require_aligned(parsed, field="sample")


if __name__ == "__main__":
    unittest.main()
