import json
import tempfile
import unittest
from pathlib import Path
from gridpulse.engine import DemandSnapshot
from gridpulse.io import CatalogError, QueryError, load_catalog, parse_query

ROOT = Path(__file__).resolve().parents[1]


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(ROOT / 'fixtures/sites.csv', ROOT / 'fixtures/sessions.csv')

    def test_catalog_types_and_count(self):
        self.assertEqual(len(self.catalog.sites), 6)
        self.assertEqual(len(self.catalog.revisions), 32)

    def test_replayed_revision_is_collapsed(self):
        self.assertEqual(len([r for r in self.catalog.revisions if r.session_id == 'S-17']), 1)

    def test_later_revision_preserved_for_candidate(self):
        self.assertEqual({r.revision for r in self.catalog.revisions if r.session_id == 'S-08'}, {1, 2, 3})

    def test_valid_query_fields(self):
        query = parse_query('{"request_id":"x","site_id":"EAST-DEPOT","from_ms":1,"until_ms":2}', self.catalog.sites)
        self.assertEqual((query.site_id, query.from_ms, query.until_ms), ('EAST-DEPOT', 1, 2))

    def test_boolean_is_not_a_timestamp(self):
        with self.assertRaises(QueryError) as ctx:
            parse_query('{"request_id":"x","site_id":"EAST-DEPOT","from_ms":true,"until_ms":2}', self.catalog.sites)
        self.assertEqual(ctx.exception.reason, 'invalid_query')

    def test_unknown_site(self):
        with self.assertRaises(QueryError) as ctx:
            parse_query('{"request_id":"x","site_id":"UNKNOWN","from_ms":1,"until_ms":2}', self.catalog.sites)
        self.assertEqual(ctx.exception.reason, 'unknown_site')

    def test_conflicting_replay_fails_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sessions.csv'
            path.write_text('session_id,revision,site_id,mode,start_ms,end_ms,kw\nA,1,EAST-DEPOT,upsert,1,5,5\nA,1,EAST-DEPOT,upsert,1,5,6\n')
            with self.assertRaises(CatalogError):
                load_catalog(ROOT / 'fixtures/sites.csv', path)

    def test_engine_interface_exists_without_implementation(self):
        query = parse_query('{"request_id":"x","site_id":"EAST-DEPOT","from_ms":1,"until_ms":2}', self.catalog.sites)
        response = DemandSnapshot(self.catalog).evaluate(query)
        self.assertEqual(response['status'], 'not_implemented')
        self.assertEqual(response['request_id'], 'x')


if __name__ == '__main__':
    unittest.main()
