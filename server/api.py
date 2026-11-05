"""Minimal JSON API and static-file server for the existing directory."""
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .store import WorkOrders, StoreError

PUBLIC = Path(__file__).resolve().parent.parent / "public"
MAX_REQUEST = 16 * 1024


def create_handler(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def handle_error(self, error):
            self.send_json(error.status, {"error": {"code": error.code,
                                                      "message": error.message}})

        def body(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_REQUEST:
                    raise ValueError()
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError()
                return body
            except (ValueError, UnicodeError, json.JSONDecodeError):
                raise StoreError(400, "BAD_JSON", "Expected a small JSON object")

        def parsed(self):
            parsed = urlsplit(self.path)
            q = parse_qs(parsed.query)
            return parsed.path, {key: value[0] for key, value in q.items()}

        def do_GET(self):
            try:
                path, params = self.parsed()
                if path == "/api/catalog":
                    return self.send_json(200, store.catalog())
                if path == "/api/jobs":
                    raw_limit = params.get("limit", "50")
                    if not raw_limit.isdigit() or not 1 <= int(raw_limit) <= 100:
                        raise StoreError(400, "BAD_LIMIT", "limit must be 1..100")
                    return self.send_json(200, store.list_jobs(
                        params.get("account", ""), params.get("search", ""),
                        params.get("status", ""), int(raw_limit)))
                match = re.fullmatch(r"/api/jobs/([A-Za-z0-9-]+)", path)
                if match:
                    return self.send_json(200, store.detail(params.get("account", ""), match.group(1)))
                if path.startswith("/api/"):
                    raise StoreError(404, "NOT_FOUND", "Unknown route")
                return self.static(path)
            except StoreError as error:
                return self.handle_error(error)

        def do_PATCH(self):
            try:
                path, params = self.parsed()
                match = re.fullmatch(r"/api/jobs/([A-Za-z0-9-]+)/note", path)
                if not match:
                    raise StoreError(404, "NOT_FOUND", "Unknown route")
                body = self.body()
                return self.send_json(200, store.note(params.get("account", ""),
                    match.group(1), body.get("note"), body.get("expectedRevision")))
            except StoreError as error:
                return self.handle_error(error)

        def do_POST(self):
            self.send_json(404, {"error": {"code": "NOT_FOUND", "message": "Unknown route"}})

        def static(self, path):
            if path == "/":
                path = "/index.html"
            if not path.startswith("/") or ".." in path or "\\" in path:
                raise StoreError(404, "NOT_FOUND", "File not found")
            file = PUBLIC / path.lstrip("/")
            if not file.is_file():
                raise StoreError(404, "NOT_FOUND", "File not found")
            content = file.read_bytes()
            content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return Handler


def serve(port=8080, store=None):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), create_handler(store or WorkOrders()))
    print(f"ServiceClock running at http://127.0.0.1:{httpd.server_port}", flush=True)
    httpd.serve_forever()
