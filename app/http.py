"""Dependency-free HTTP interface for the contract directory."""
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from . import store

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'

class Handler(BaseHTTPRequestHandler):
    db_path = store.DB

    def respond(self, status, obj):
        content = json.dumps(obj, separators=(',', ':')).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def serve_static(self, path):
        assets = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/styles.css': ('styles.css', 'text/css')}
        if path not in assets:
            return self.respond(404, {'error': 'Not found'})
        name, kind = assets[path]
        content = (PUBLIC / name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        one = lambda name, default='': query.get(name, [default])[0]
        try:
            if url.path == '/api/catalog':
                return self.respond(200, store.catalog())
            if url.path == '/api/contracts':
                try:
                    offset, limit = int(one('offset', '0')), int(one('limit', '30'))
                except ValueError:
                    raise store.DomainError(400, 'Invalid pagination')
                return self.respond(200, store.list_contracts(one('org'), one('q'), one('status'), offset, limit, self.db_path))
            match = re.fullmatch(r'/api/contracts/([a-zA-Z0-9-]+)', url.path)
            if match:
                return self.respond(200, store.get_contract(match[1], one('org'), self.db_path))
            return self.serve_static(url.path)
        except store.DomainError as error:
            self.respond(error.status, {'error': str(error), 'current': error.current})

    def do_PATCH(self):
        url = urlparse(self.path)
        match = re.fullmatch(r'/api/contracts/([a-zA-Z0-9-]+)/note', url.path)
        if not match:
            return self.respond(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 1 or length > 65536:
                raise store.DomainError(400, 'Invalid body length')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise store.DomainError(400, 'Expected an object')
            result = store.edit_note(match[1], data.get('orgId'), data.get('expectedRevision'), data.get('note'), self.db_path)
            self.respond(200, result)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self.respond(400, {'error': 'Malformed JSON'})
        except store.DomainError as error:
            self.respond(error.status, {'error': str(error), 'current': error.current})

def run():
    path = Path(os.environ.get('CYCLELEDGER_DB', str(store.DB)))
    store.initialize(path)
    Handler.db_path = path
    port = int(os.environ.get('PORT', '8080'))
    print(f'CycleLedger listening on http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()

if __name__ == '__main__':
    run()
