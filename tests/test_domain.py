import unittest
from app.domain import Store, StaleRevision
from app.loaders import load_fixtures

class DomainTests(unittest.TestCase):
    def setUp(self):
        endpoints, deliveries = load_fixtures()
        self.store = Store(endpoints, deliveries)

    def test_list_order_and_filters(self):
        got = self.store.list_endpoints(status="enabled")
        self.assertEqual(3, len(got))
        self.assertEqual(("acme", "Billing events"), (got[0]["tenant"], got[0]["name"]))
        self.assertEqual(2, len(self.store.list_endpoints(tenant="acme")))

    def test_detail_newest_first(self):
        detail = self.store.get_endpoint("ep_acme_billing")
        rows = detail["deliveries"]
        self.assertGreaterEqual(rows[0]["receivedAt"], rows[1]["receivedAt"])

    def test_status_change_and_noop_revision(self):
        detail = self.store.get_endpoint("ep_acme_billing")
        before = detail["endpoint"]
        changed = self.store.set_enabled("ep_acme_billing", False, before["revision"])
        self.assertTrue(changed["changed"])
        self.assertEqual(before["revision"] + 1, changed["endpoint"]["revision"])
        self.assertEqual(before["datasetRevision"] + 1, changed["endpoint"]["datasetRevision"])
        noop = self.store.set_enabled("ep_acme_billing", False, changed["endpoint"]["revision"])
        self.assertFalse(noop["changed"])
        self.assertEqual(changed["endpoint"]["revision"], noop["endpoint"]["revision"])
        self.assertEqual(changed["endpoint"]["datasetRevision"], noop["endpoint"]["datasetRevision"])

    def test_stale_status_rejected_without_mutation(self):
        before = self.store.get_endpoint("ep_acme_billing")["endpoint"]
        with self.assertRaises(StaleRevision):
            self.store.set_enabled("ep_acme_billing", False, 1)
        after = self.store.get_endpoint("ep_acme_billing")["endpoint"]
        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main()
