from __future__ import annotations

import uuid
from .store import Store
from .models import CreditEvent

class DomainError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


def find_account(store: Store, account_id: str):
    return next((a for a in store.accounts if a.id == account_id), None)


def list_account_invoices(store: Store, account_id: str):
    return [i for i in store.invoices if i.account_id == account_id]


def record_manual_credit(store: Store, account_id: str, amount_cents: int, reason: str):
    if amount_cents <= 0:
        raise DomainError('amountCents must be positive', 'invalid_amount')
    if not reason.strip():
        raise DomainError('reason is required', 'invalid_reason')

    account = find_account(store, account_id)
    if not account:
        raise DomainError('account not found', 'account_not_found', 404)

    with store.lock:
        account.credit_cents += amount_cents
        account.revision += 1
        event = CreditEvent(
            id=f'credit_{uuid.uuid4().hex[:8]}',
            account_id=account.id,
            amount_cents=amount_cents,
            reason=reason.strip(),
        )
        store.credit_events.append(event)
        return {'account': account.to_dict(), 'event': event.to_dict()}
