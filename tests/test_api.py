import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from server.api import create_handler
from server.store import WorkOrders

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(WorkOrders()))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=3)

    def read(self, path, method="GET", payload=None):
        request = Request(self.base + path, method=method,
                          headers={"Content-Type": "application/json"},
                          data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_catalog_and_list(self):
        code, data = self.read("/api/jobs?account=acme&limit=1")
        self.assertEqual(code, 200); self.assertEqual(len(data["jobs"]), 1)
        self.assertGreater(data["total"], 1)

    def test_notes_over_http(self):
        code, detail = self.read("/api/jobs/WO-101?account=acme")
        self.assertEqual(code, 200)
        revision = detail["job"]["revision"]
        code, value = self.read("/api/jobs/WO-101/note?account=acme", "PATCH",
                                {"note": "HTTP note", "expectedRevision": revision})
        self.assertEqual(code, 200); self.assertEqual(value["job"]["revision"], revision + 1)
        code, bad = self.read("/api/jobs/WO-101/note?account=acme", "PATCH",
                              {"note": "stale", "expectedRevision": revision})
        self.assertEqual(code, 409); self.assertEqual(bad["error"]["code"], "STALE_REVISION")

    def test_not_found_does_not_expose_other_account(self):
        code, _ = self.read("/api/jobs/WO-202?account=acme")
        self.assertEqual(code, 404)

    def test_static_frontend(self):
        with urlopen(self.base + "/", timeout=4) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"ServiceClock", response.read())
