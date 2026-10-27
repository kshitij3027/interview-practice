import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from permitlens.store import VisitStore
from server import make_handler

BASE = Path(__file__).resolve().parents[1]


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = VisitStore(BASE / 'fixtures/workspace.json', BASE / 'fixtures/credentials.jsonl')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(cls.store))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, method='GET', body=None):
        data = None if body is None else json.dumps(body).encode()
        req = Request(self.base + path, method=method, data=data, headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=3) as result:
                raw = result.read()
                return result.status, json.loads(raw) if result.headers.get_content_type() == 'application/json' else raw.decode()
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_health_and_tenants(self):
        code, value = self.request('/api/health')
        self.assertEqual((code, value['ok']), (200, True))
        code, value = self.request('/api/tenants')
        self.assertEqual(value['tenants'], ['harbor', 'orchid'])

    def test_list_detail_and_static_app(self):
        code, value = self.request('/api/visits?tenant=harbor&status=confirmed')
        self.assertEqual((code, value['total']), (200, 1))
        code, value = self.request('/api/visits/VIS-001?tenant=harbor')
        self.assertEqual((code, value['visit']['vendorName']), (200, 'Apex Mechanical'))
        code, html = self.request('/')
        self.assertIn('PermitLens', html)
        code, javascript = self.request('/app.js')
        self.assertIn('loadList', javascript)

    def test_note_route_and_replay_conflict(self):
        _, detail = self.request('/api/visits/VIS-010?tenant=orchid')
        revision = detail['visit']['revision']
        code, updated = self.request('/api/visits/VIS-010/note?tenant=orchid', 'PATCH', {'note': '  Coordination pending  ', 'expectedRevision': revision})
        self.assertEqual((code, updated['visit']['note']), (200, 'Coordination pending'))
        code, failed = self.request('/api/visits/VIS-010/note?tenant=orchid', 'PATCH', {'note': 'bad', 'expectedRevision': revision})
        self.assertEqual((code, failed['error']['code']), (409, 'stale_revision'))

    def test_scope_and_bad_inputs(self):
        self.assertEqual(self.request('/api/visits/VIS-010?tenant=harbor')[0], 404)
        self.assertEqual(self.request('/api/visits?tenant=harbor&limit=0')[0], 400)
        self.assertEqual(self.request('/api/visits?tenant=harbor&status=invalid')[0], 400)
        self.assertEqual(self.request('/api/visits?tenant=harbor&delayMs=5000')[0], 400)
        self.assertEqual(self.request('/api/missing')[0], 404)


if __name__ == '__main__':
    unittest.main()
