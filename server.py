"""HTTP entry point for the PermitLens operations workspace."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from permitlens.store import DomainError, VisitStore

BASE = Path(__file__).resolve().parent
WEB = BASE / "frontend"


def make_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _param(self, params, name, default=None):
            return params.get(name, [default])[-1]

        def _delay(self, params):
            raw = self._param(params, "delayMs", "0")
            if not raw.isdecimal() or int(raw) > 1000:
                raise DomainError(400, "invalid_delay", "delayMs must be 0 to 1000.")
            time.sleep(int(raw) / 1000)

        def _body(self):
            length = self.headers.get("Content-Length", "")
            if not length.isdecimal() or int(length) > 65536:
                raise DomainError(400, "invalid_body", "Expected a JSON body of at most 65536 bytes.")
            try:
                return json.loads(self.rfile.read(int(length)))
            except (ValueError, UnicodeDecodeError):
                raise DomainError(400, "invalid_json", "Body must contain valid JSON.")

        def _static(self, pathname):
            routes = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/api.js": "api.js", "/styles.css": "styles.css"}
            filename = routes.get(pathname)
            if not filename:
                raise DomainError(404, "not_found", "Resource not found.")
            data = (WEB / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", (mimetypes.guess_type(filename)[0] or "text/plain") + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _handle(self, method):
            try:
                url = urlparse(self.path)
                params = parse_qs(url.query, keep_blank_values=True)
                path = unquote(url.path)
                if method == "GET" and path == "/api/health":
                    return self._send(200, {"ok": True, "service": "permitlens"})
                if method == "GET" and path == "/api/tenants":
                    return self._send(200, {"tenants": store.tenants})
                if method == "GET" and path == "/api/visits":
                    self._delay(params)
                    raw_limit = self._param(params, "limit", "100")
                    if not raw_limit.isdecimal():
                        raise DomainError(400, "invalid_limit", "Limit must be a positive integer.")
                    return self._send(200, store.list_visits(self._param(params, "tenant"), self._param(params, "status", "all"), self._param(params, "q", ""), int(raw_limit)))
                visit_match = re.fullmatch(r"/api/visits/([A-Za-z0-9-]+)(/note)?", path)
                if visit_match:
                    visit_id = visit_match.group(1)
                    tenant = self._param(params, "tenant")
                    if method == "GET" and visit_match.group(2) is None:
                        self._delay(params)
                        return self._send(200, store.get_visit(tenant, visit_id))
                    if method == "PATCH" and visit_match.group(2) == "/note":
                        return self._send(200, store.update_note(tenant, visit_id, self._body()))
                if method == "GET" and not path.startswith("/api/"):
                    return self._static(path)
                raise DomainError(404, "not_found", "Endpoint not found.")
            except DomainError as exc:
                return self._send(exc.status, {"error": {"code": exc.code, "message": str(exc), "details": exc.details}})
            except (BrokenPipeError, ConnectionResetError):
                return

        def do_GET(self):
            self._handle("GET")

        def do_PATCH(self):
            self._handle("PATCH")

        def do_POST(self):
            self._handle("POST")

        def log_message(self, format, *args):
            if os.getenv("PERMITLENS_LOG_HTTP"):
                super().log_message(format, *args)

    return Handler


def serve(port=8080):
    store = VisitStore(BASE / "fixtures/workspace.json", BASE / "fixtures/credentials.jsonl")
    server = ThreadingHTTPServer(("0.0.0.0", int(port)), make_handler(store))
    print(f"PermitLens running on http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve(int(os.getenv("PORT", "8080")))
