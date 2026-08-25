from .http_helpers import query_params, read_json, send_json

class Routes:
    def __init__(self, service):
        self.service = service

    def handle_get(self, handler):
        path, query = query_params(handler.path)
        if path == "/api/health":
            return send_json(handler, 200, {"ok": True})
        if path == "/api/cases":
            try:
                cases = self.service.list_cases(query.get("status"), query.get("priority"))
                return send_json(handler, 200, {"cases": cases})
            except ValueError as exc:
                return send_json(handler, 400, {"error": str(exc)})
        if path.startswith("/api/cases/"):
            case_id = path.split("/")[3]
            case = self.service.get_case(case_id)
            if not case:
                return send_json(handler, 404, {"error": "case_not_found"})
            return send_json(handler, 200, {"case": case})
        return send_json(handler, 404, {"error": "not_found"})

    def handle_post(self, handler):
        path, _ = query_params(handler.path)
        if path.startswith("/api/cases/") and path.endswith("/notes"):
            case_id = path.split("/")[3]
            try:
                payload = read_json(handler)
                case = self.service.add_note(case_id, payload.get("text"), payload.get("expected_revision"))
                return send_json(handler, 200, {"case": case})
            except KeyError as exc:
                return send_json(handler, 404, {"error": exc.args[0]})
            except ValueError as exc:
                code = str(exc)
                return send_json(handler, 409 if code == "stale_revision" else 400, {"error": code})
            except Exception:
                return send_json(handler, 400, {"error": "invalid_json"})
        return send_json(handler, 404, {"error": "not_found"})
