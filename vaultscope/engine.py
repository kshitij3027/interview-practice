"""Access audit component. Implement the customer capability here."""


class VaultScope:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def decide(self, query):
        """Return the documented decision response for one validated query."""
        return {
            "query_id": query["query_id"],
            "status": "ok",
            "decision": "none",
            "policy_id": None,
            "via": [],
        }
