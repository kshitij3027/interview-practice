from __future__ import annotations
import json, mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .store import FlagStore, NotFound, StaleRevision, ValidationError

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"

def make_handler(store: FlagStore):
    class Handler(BaseHTTPRequestHandler):
        server_version = "FlagDesk/1.0"
        def log_message(self, fmt: str, *args): return

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                return self._json(HTTPStatus.OK, {"ok": True})
            if parsed.path == "/api/flags":
                qs = parse_qs(parsed.query)
                status = self._single(qs, "status")
                owner = self._single(qs, "owner")
                return self._json(HTTPStatus.OK, store.list_flags(status=status, owner=owner))
            if parsed.path.startswith("/api/flags/"):
                flag_id = parsed.path.removeprefix("/api/flags/")
                if "/" not in flag_id:
                    try:
                        return self._json(HTTPStatus.OK, {
                            "datasetRevision": store.dataset_revision,
                            "flag": store.get_flag(flag_id),
                        })
                    except NotFound:
                        return self._json(HTTPStatus.NOT_FOUND, {"error": "flag not found"})
            return self._static(parsed.path)

        def do_PATCH(self):
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/flags/") and parsed.path.endswith("/note"):
                flag_id = parsed.path[len("/api/flags/"):-len("/note")]
                try:
                    body = self._read_json()
                    expected, note = body.get("expectedRevision"), body.get("note")
                    if not isinstance(expected, int) or not isinstance(note, str):
                        raise ValidationError("expectedRevision must be integer and note must be string")
                    return self._json(HTTPStatus.OK, store.update_note(flag_id, expected, note))
                except NotFound:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "flag not found"})
                except ValidationError as exc:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                except StaleRevision as exc:
                    return self._json(HTTPStatus.CONFLICT, {"error": "stale revision", "current": exc.current})
                except (json.JSONDecodeError, ValueError):
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON body"})
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        @staticmethod
        def _single(qs, key):
            values = qs.get(key)
            return values[0] if values and values[0] else None

        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

        def _json(self, status, payload):
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _static(self, path):
            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            file_path = (STATIC / relative).resolve()
            if not str(file_path).startswith(str(STATIC.resolve())) or not file_path.is_file():
                return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    return Handler

def serve(host="127.0.0.1", port=8080):
    store = FlagStore(ROOT / "fixtures" / "flags.json")
    ThreadingHTTPServer((host, port), make_handler(store)).serve_forever()
