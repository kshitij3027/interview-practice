import os
from .api import serve

if __name__ == "__main__":
    serve(int(os.environ.get("PORT", "8080")))
