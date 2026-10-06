import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from app.domain import Store
from app.httpapi import handler_for
from app.loaders import load_fixtures

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        endpoints, deliveries = load_fixtures()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(Store(endpoints, deliveries)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def request(self, method, path, body=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        payload = None if body is None else json.dumps(body)
        conn.request(method, path, body=payload, headers={"content-type":"application/json"})
        res = conn.getresponse(); data = json.loads(res.read() or b"{}"); conn.close()
        return res.status, data

    def test_health_and_paused_filter(self):
        status, body = self.request("GET", "/api/health")
        self.assertEqual(200, status); self.assertTrue(body["ok"])
        status, body = self.request("GET", "/api/endpoints?status=paused")
        self.assertEqual(200, status); self.assertEqual(["Partner CRM"], [x["name"] for x in body["items"]])

    def test_stale_returns_current(self):
        status, body = self.request("POST", "/api/endpoints/ep_acme_billing/status", {"enabled":False,"expectedRevision":1})
        self.assertEqual(409, status); self.assertEqual("stale_revision", body["error"]["code"]); self.assertGreater(body["error"]["current"]["revision"], 1)

if __name__ == "__main__":
    unittest.main()
