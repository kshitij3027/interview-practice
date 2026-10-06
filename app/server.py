import os
from http.server import ThreadingHTTPServer
from .domain import Store
from .httpapi import handler_for
from .loaders import load_fixtures

def main():
    endpoints, deliveries = load_fixtures()
    store = Store(endpoints, deliveries)
    port = int(os.environ.get("PORT", "8080"))
    print(f"PulseReplay listening on http://localhost:{port}")
    ThreadingHTTPServer(("", port), handler_for(store)).serve_forever()

if __name__ == "__main__":
    main()
