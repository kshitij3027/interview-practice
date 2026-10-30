"""Site-level demand assessment entry point."""
from .model import Catalog, Query


class DemandSnapshot:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def evaluate(self, query: Query) -> dict:
        return {"request_id": query.request_id, "status": "not_implemented"}
