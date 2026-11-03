import unittest
from fastapi.testclient import TestClient
from app.api import make_app
from app.store import LotStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(make_app(LotStore()))

    def test_browser_root_and_meta(self):
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn('BatchGuard', page.text)
        self.assertEqual(len(self.client.get('/api/meta').json()['plants']), 3)

    def test_lots_and_details(self):
        self.assertEqual(self.client.get('/api/lots?status=open').json()['total'], 10)
        self.assertEqual(self.client.get('/api/lots/LOT-1004').json()['lot']['status'], 'closed')

    def test_note_http_contract_and_conflict(self):
        url = '/api/lots/LOT-1002/note'
        reply = self.client.patch(url, json={'note':' new note ', 'expectedRevision':2})
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json()['lot']['note'], 'new note')
        self.assertEqual(self.client.patch(url, json={'note':' stale ', 'expectedRevision':2}).status_code, 409)
        self.assertEqual(self.client.get('/api/lots/LOT-1002').json()['lot']['revision'], 3)

    def test_errors_structured(self):
        self.assertEqual(self.client.get('/api/lots/NOT-FOUND').json()['error']['code'], 'LOT_NOT_FOUND')
        self.assertEqual(self.client.patch('/api/lots/LOT-1001/note', content=b'not json').status_code, 400)


if __name__ == '__main__': unittest.main()
