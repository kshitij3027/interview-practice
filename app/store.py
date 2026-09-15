import csv
import json
from pathlib import Path
from threading import RLock

from .models import BudgetChange, Campaign, SpendEvent


class ConflictError(Exception):
    def __init__(self, campaign):
        super().__init__("stale campaign revision")
        self.campaign = campaign


class ValidationError(Exception):
    pass


class CampaignStore:
    def __init__(self, fixture_dir: Path):
        self._lock = RLock()
        self.fixture_dir = Path(fixture_dir)
        self.dataset_revision = 7
        self.campaigns = self._load_campaigns()
        self.budget_changes = self._load_budget_changes()
        self.spend_events = self._load_spend_events()

    def _load_campaigns(self):
        rows = json.loads((self.fixture_dir / "campaigns.json").read_text())
        return {row["id"]: Campaign(**row) for row in rows}

    def _load_budget_changes(self):
        with (self.fixture_dir / "budget_changes.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        return [
            BudgetChange(
                campaign_id=row["campaign_id"],
                effective_at=row["effective_at"],
                daily_budget_cents=int(row["daily_budget_cents"]),
            )
            for row in rows
        ]

    def _load_spend_events(self):
        events = []
        for line in (self.fixture_dir / "spend_events.jsonl").read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            events.append(SpendEvent(**row))
        return events

    def list_campaigns(self, status=None):
        with self._lock:
            items = list(self.campaigns.values())
            if status:
                items = [item for item in items if item.status == status]
            items.sort(key=lambda item: (item.account_name.lower(), item.id))
            return [item.to_dict() for item in items]

    def get_campaign(self, campaign_id):
        with self._lock:
            campaign = self.campaigns.get(campaign_id)
            if campaign is None:
                return None
            result = campaign.to_dict()
            result["budget_changes"] = [
                change.to_dict()
                for change in sorted(
                    (c for c in self.budget_changes if c.campaign_id == campaign_id),
                    key=lambda c: c.effective_at,
                )
            ]
            result["dataset_revision"] = self.dataset_revision
            return result

    def set_status(self, campaign_id, status, expected_revision):
        if status not in {"active", "paused"}:
            raise ValidationError("status must be active or paused")
        with self._lock:
            campaign = self.campaigns.get(campaign_id)
            if campaign is None:
                return None
            if campaign.revision != expected_revision:
                raise ConflictError(self.get_campaign(campaign_id))
            if campaign.status != status:
                campaign.status = status
                campaign.revision += 1
                self.dataset_revision += 1
            return self.get_campaign(campaign_id)
