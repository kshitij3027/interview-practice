"""Candidate-facing fulfillment interface; the strategy is intentionally open."""


class FreshClaim:
    def __init__(self, inventory):
        self.inventory = inventory

    def assess(self, request):
        # Your customer capability goes here. Choose the representation and approach.
        return {"request_id": request["request_id"], "status": "not_implemented"}
