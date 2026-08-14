from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

InvoiceStatus = Literal['open', 'paid']

@dataclass
class Account:
    id: str
    external_id: str
    name: str
    credit_cents: int
    revision: int

    def to_dict(self):
        return asdict(self)

@dataclass
class Invoice:
    id: str
    account_id: str
    due_date: str
    original_cents: int
    remaining_cents: int
    status: InvoiceStatus

    def to_dict(self):
        return asdict(self)

@dataclass
class CreditEvent:
    id: str
    account_id: str
    amount_cents: int
    reason: str

    def to_dict(self):
        return asdict(self)
