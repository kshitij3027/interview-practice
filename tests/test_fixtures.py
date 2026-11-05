import datetime as dt
import unittest
from zoneinfo import ZoneInfo
from server.data import load_workspace, load_activity

class FixtureTests(unittest.TestCase):
    def test_references_and_timezones(self):
        doc = load_workspace()
        accounts = {a["id"] for a in doc["accounts"]}
        sites = {s["id"]: s for s in doc["sites"]}
        self.assertEqual(len(doc["jobs"]), 12)
        for site in sites.values():
            ZoneInfo(site["timeZone"])
            self.assertIn(site["accountId"], accounts)
        for job in doc["jobs"]:
            self.assertEqual(job["accountId"], sites[job["siteId"]]["accountId"])
            self.assertIn(job["priority"], doc["priorities"])
            self.assertIsNotNone(dt.datetime.fromisoformat(job["openedAt"].replace("Z", "+00:00")).tzinfo)

    def test_feed_contains_realistic_quirks(self):
        feed = load_activity()
        self.assertGreaterEqual(len(feed), 20)
        self.assertNotEqual([e.get("occurredAt") for e in feed],
                            sorted(e.get("occurredAt", "") for e in feed))
        ids = [row.get("eventId") for row in feed]
        self.assertLess(len(set(ids)), len(ids))
