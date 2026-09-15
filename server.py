import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.http import AppHandlerMixin
from app.service import CampaignService
from app.store import CampaignStore


ROOT = Path(__file__).resolve().parent


class Handler(AppHandlerMixin, SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if os.environ.get("QUIET") != "1":
            super().log_message(fmt, *args)


def create_server(host="127.0.0.1", port=8080):
    store = CampaignStore(ROOT / "fixtures")
    service = CampaignService(store)
    Handler.service = service
    Handler.web_dir = ROOT / "web"
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = create_server(port=port)
    print(f"PaceDesk running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
