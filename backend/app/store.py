from __future__ import annotations

from copy import deepcopy
from threading import Lock
from .models import Account, Invoice, CreditEvent

INITIAL_ACCOUNTS = [
    Account('acct_1', 'ACME-001', 'Acme North', 0, 7),
    Account('acct_2', 'BRIGHT-44', 'Bright Retail', 1250, 3),
    Account('acct_3', 'CLOUD-9', 'Cloud Nine Labs', 0, 11),
]

INITIAL_INVOICES = [
    Invoice('inv_100', 'acct_1', '2026-07-01', 9000, 9000, 'open'),
    Invoice('inv_101', 'acct_1', '2026-07-15', 5000, 5000, 'open'),
    Invoice('inv_200', 'acct_2', '2026-06-20', 7000, 2500, 'open'),
    Invoice('inv_201', 'acct_2', '2026-08-01', 4000, 4000, 'open'),
    Invoice('inv_300', 'acct_3', '2026-07-10', 10000, 0, 'paid'),
    Invoice('inv_301', 'acct_3', '2026-08-05', 8000, 8000, 'open'),
]

class Store:
    def __init__(self):
        self.lock = Lock()
        self.reset()

    def reset(self):
        self.accounts = deepcopy(INITIAL_ACCOUNTS)
        self.invoices = deepcopy(INITIAL_INVOICES)
        self.credit_events: list[CreditEvent] = []

    def snapshot(self):
        return {
            'accounts': [a.to_dict() for a in self.accounts],
            'invoices': [i.to_dict() for i in self.invoices],
            'creditEvents': [e.to_dict() for e in self.credit_events],
        }

store = Store()
