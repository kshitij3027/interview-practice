import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from src.routes import Routes
from src.service import CaseService
from src.store import CaseStore

class HandlerFactory:
    @staticmethod
    def make(routes):
        from http.server import BaseHTTPRequestHandler
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self): routes.handle_get(self)
            def do_POST(self): routes.handle_post(self)
            def log_message(self, format, *args): pass
        return Handler

class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = Routes(CaseService(CaseStore()))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), HandlerFactory.make(cls.routes))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls): cls.server.shutdown()

    def request(self, method, path, payload=None):
        conn = HTTPConnection("127.0.0.1", self.port)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type":"application/json"} if body else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
        return response.status, data

    def test_lists_cases(self):
        status, data = self.request("GET", "/api/cases?status=open")
        self.assertEqual(status, 200)
        self.assertTrue(all(c["status"] == "open" for c in data["cases"]))

    def test_add_note_and_stale_conflict(self):
        _, detail = self.request("GET", "/api/cases/c-103")
        revision = detail["case"]["revision"]
        status, data = self.request("POST", "/api/cases/c-103/notes", {"text":"investigating", "expected_revision":revision})
        self.assertEqual(status, 200)
        stale_status, stale = self.request("POST", "/api/cases/c-103/notes", {"text":"again", "expected_revision":revision})
        self.assertEqual(stale_status, 409)
        self.assertEqual(stale["error"], "stale_revision")

if __name__ == "__main__": unittest.main()
