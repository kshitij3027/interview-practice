"""Customer attribution capability."""


class SourceAttributor:
    def __init__(self, catalog):
        self.catalog = catalog

    def assess(self, request):
        return {"request_id": request.request_id, "status": "not_implemented"}
