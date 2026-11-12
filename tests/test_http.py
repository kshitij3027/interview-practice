import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from app import store
from app.http import Handler

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = store.initialize(Path(cls.temp.name)/'http.sqlite')
        Handler.db_path = cls.db
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, path, method='GET', body=None):
        request = Request(self.url+path, method=method, data=json.dumps(body).encode() if body is not None else None, headers={'Content-Type':'application/json'})
        try:
            with urlopen(request) as res: return res.status, res.read(), res.headers.get('Content-Type')
        except HTTPError as exc: return exc.code, exc.read(), exc.headers.get('Content-Type')

    def test_static_assets(self):
        for name in ['/', '/app.js', '/styles.css']:
            status,data,_=self.request(name)
            self.assertEqual(status,200)
            self.assertTrue(len(data)>100)

    def test_catalog_and_contract_details(self):
        status,data,_=self.request('/api/catalog')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(data)['plans']),3)
        status,data,_=self.request('/api/contracts/ctr-104?org=org-cedar')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['seats'],120)

    def test_http_note_conflict(self):
        status,data,_=self.request('/api/contracts/ctr-102/note', 'PATCH', {'orgId':'org-cedar','expectedRevision':2,'note':'Approved'})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['revision'],3)
        status,data,_=self.request('/api/contracts/ctr-102/note', 'PATCH', {'orgId':'org-cedar','expectedRevision':2,'note':'Old'})
        self.assertEqual(status,409)
        self.assertEqual(json.loads(data)['current']['note'],'Approved')

    def test_unknown_route(self):
        self.assertEqual(self.request('/api/not-real')[0],404)

if __name__ == '__main__': unittest.main()
