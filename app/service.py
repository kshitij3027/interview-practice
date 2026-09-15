from .store import CampaignStore


class CampaignService:
    def __init__(self, store: CampaignStore):
        self.store = store

    def list_campaigns(self, status=None):
        if status not in {None, "", "active", "paused"}:
            raise ValueError("unsupported status filter")
        return {
            "campaigns": self.store.list_campaigns(status or None),
            "dataset_revision": self.store.dataset_revision,
        }

    def get_campaign(self, campaign_id):
        return self.store.get_campaign(campaign_id)

    def update_status(self, campaign_id, status, expected_revision):
        return self.store.set_status(campaign_id, status, expected_revision)
