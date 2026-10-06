import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .domain import NotFound, StaleRevision

MAX_BODY = 4096

def handler_for(store, web_root="web"):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _json(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _error(self, status, code, message, current=None):
            self._json(status, {"error": {"code": code, "message": message, "current": current}})

        def _body(self):
            length = int(self.headers.get("content-length", "0") or 0)
            if length > MAX_BODY:
                raise ValueError("body too large")
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                return self._json(200, {"ok": True})
            if parsed.path == "/api/endpoints":
                q = parse_qs(parsed.query)
                tenant = q.get("tenant", [""])[0].strip()
                status = q.get("status", [""])[0].strip()
                if status not in {"", "enabled", "paused"}:
                    return self._error(400, "invalid_status", "status must be enabled or paused")
                return self._json(200, {"items": store.list_endpoints(tenant, status)})
            if parsed.path.startswith("/api/endpoints/"):
                endpoint_id = parsed.path.removeprefix("/api/endpoints/")
                if "/" not in endpoint_id:
                    try:
                        return self._json(200, store.get_endpoint(endpoint_id))
                    except NotFound:
                        return self._error(404, "endpoint_not_found", "endpoint not found")
            return self._serve_static(parsed.path)

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/endpoints/") and parsed.path.endswith("/status"):
                endpoint_id = parsed.path[len("/api/endpoints/"):-len("/status")]
                try:
                    body = self._body()
                except Exception:
                    return self._error(400, "invalid_json", "invalid JSON")
                if type(body.get("enabled")) is not bool:
                    return self._error(400, "invalid_enabled", "enabled must be boolean")
                if type(body.get("expectedRevision")) is not int or body["expectedRevision"] < 1:
                    return self._error(400, "invalid_revision", "expectedRevision must be positive")
                try:
                    return self._json(200, store.set_enabled(endpoint_id, body["enabled"], body["expectedRevision"]))
                except NotFound:
                    return self._error(404, "endpoint_not_found", "endpoint not found")
                except StaleRevision as exc:
                    return self._error(409, "stale_revision", "endpoint changed; refresh and retry", exc.current)
            return self._error(404, "not_found", "route not found")

        def _serve_static(self, path):
            from pathlib import Path
            rel = "index.html" if path in {"", "/"} else path.lstrip("/")
            root = Path(web_root).resolve()
            target = (root / rel).resolve()
            if root not in target.parents and target != root:
                return self._error(404, "not_found", "not found")
            if not target.is_file():
                return self._error(404, "not_found", "not found")
            ctype = "text/html" if target.suffix == ".html" else "text/javascript" if target.suffix == ".js" else "text/css"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("content-type", ctype)
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    return Handler
