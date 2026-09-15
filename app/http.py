import json
import mimetypes
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .store import ConflictError, ValidationError


class AppHandlerMixin:
    service = None
    web_dir = None

    def _json(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            raise ValidationError("invalid JSON body")

    def _parts(self):
        parsed = urlparse(self.path)
        return parsed, [part for part in parsed.path.split("/") if part]

    def do_GET(self):
        parsed, parts = self._parts()
        if parsed.path == "/api/health":
            return self._json(HTTPStatus.OK, {"ok": True})
        if parsed.path == "/api/campaigns":
            try:
                status = parse_qs(parsed.query).get("status", [None])[0]
                return self._json(HTTPStatus.OK, self.service.list_campaigns(status))
            except ValueError as exc:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        if len(parts) == 3 and parts[:2] == ["api", "campaigns"]:
            campaign = self.service.get_campaign(parts[2])
            if campaign is None:
                return self._json(HTTPStatus.NOT_FOUND, {"error": "campaign not found"})
            return self._json(HTTPStatus.OK, campaign)
        return self._serve_static(parsed.path)

    def do_PATCH(self):
        parsed, parts = self._parts()
        if len(parts) == 4 and parts[:2] == ["api", "campaigns"] and parts[3] == "status":
            try:
                body = self._read_json()
                if not isinstance(body.get("expected_revision"), int):
                    raise ValidationError("expected_revision must be an integer")
                campaign = self.service.update_status(parts[2], body.get("status"), body["expected_revision"])
                if campaign is None:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "campaign not found"})
                return self._json(HTTPStatus.OK, campaign)
            except ConflictError as exc:
                return self._json(HTTPStatus.CONFLICT, {"error": "stale revision", "current": exc.campaign})
            except ValidationError as exc:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def _serve_static(self, path):
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (Path(self.web_dir) / relative).resolve()
        root = Path(self.web_dir).resolve()
        if root not in target.parents and target != root:
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        if not target.is_file():
            return self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
