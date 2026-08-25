from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from src.routes import Routes
from src.service import CaseService
from src.store import CaseStore

routes = Routes(CaseService(CaseStore()))

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        routes.handle_get(self)

    def do_POST(self):
        routes.handle_post(self)

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print("CaseBridge API listening on http://localhost:3001")
    ThreadingHTTPServer(("127.0.0.1", 3001), Handler).serve_forever()
