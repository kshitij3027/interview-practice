from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Campaign:
    id: str
    account_name: str
    name: str
    timezone: str
    status: str
    daily_budget_cents: int
    revision: int

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class BudgetChange:
    campaign_id: str
    effective_at: str
    daily_budget_cents: int

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SpendEvent:
    event_id: str
    campaign_id: str
    occurred_at: str
    ingested_at: str
    kind: str
    amount_cents: int
    replaces_event_id: Optional[str] = None
