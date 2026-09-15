import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from server import create_server


class HttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def request(self, path, method="GET", body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            method=method,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_health_and_filter(self):
        status, payload = self.request("/api/health")
        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        status, payload = self.request("/api/campaigns?status=paused")
        self.assertEqual(200, status)
        self.assertEqual(["cmp-boreal"], [c["id"] for c in payload["campaigns"]])

    def test_status_conflict_returns_current_state(self):
        status, detail = self.request("/api/campaigns/cmp-cirrus")
        self.assertEqual(200, status)
        status, payload = self.request(
            "/api/campaigns/cmp-cirrus/status",
            method="PATCH",
            body={"status": "paused", "expected_revision": detail["revision"] - 1},
        )
        self.assertEqual(409, status)
        self.assertEqual("cmp-cirrus", payload["current"]["id"])

    def test_static_index_served(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/") as response:
            text = response.read().decode()
        self.assertIn("PaceDesk", text)


if __name__ == "__main__":
    unittest.main()
