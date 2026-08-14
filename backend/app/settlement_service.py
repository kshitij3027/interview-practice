from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation

from .store import Store
from .services import DomainError

REQUIRED_COLUMNS = {'payment_id', 'customer_ref', 'amount', 'received_at', 'note'}


def parse_csv(text: str) -> list[dict]:
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return []

    header = [col.strip() for col in lines[0].split(',')]
    missing = REQUIRED_COLUMNS - set(header)
    if missing:
        raise DomainError(
            f'missing columns: {", ".join(sorted(missing))}',
            'invalid_csv',
        )

    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split(',')
        row = {
            header[i]: values[i].strip() if i < len(values) else ''
            for i in range(len(header))
        }
        rows.append(row)
    return rows


def _parse_amount_cents(amount_str: str) -> int:
    try:
        d = Decimal(amount_str)
        if d.as_tuple().exponent < -2:
            raise ValueError('more than 2 decimal places')
        if d <= 0:
            raise ValueError('must be positive')
        return int(d * 100)
    except (InvalidOperation, ValueError):
        raise DomainError(f'invalid amount: {amount_str}', 'invalid_amount')


def build_preview(store: Store, csv_text: str) -> dict:
    raw_rows = parse_csv(csv_text)

    account_lookup = {a.external_id.casefold(): a for a in store.accounts}

    # Simulate invoice state without touching the store
    invoice_remaining: dict[str, int] = {inv.id: inv.remaining_cents for inv in store.invoices}

    seen_payment_ids: dict[str, int] = {}  # payment_id → first row index
    affected_accounts: dict[str, object] = {}  # account_id → account (insertion-ordered, unique)
    account_credit_additions: dict[str, int] = {}  # credit remainder summed per account
    result_rows: list[dict] = []

    for idx, raw in enumerate(raw_rows):
        payment_id = raw.get('payment_id', '')
        customer_ref = raw.get('customer_ref', '')
        amount_str = raw.get('amount', '')

        if payment_id in seen_payment_ids:
            result_rows.append({
                'payment_id': payment_id,
                'status': 'duplicate',
                'error': f'duplicate of first occurrence at row {seen_payment_ids[payment_id] + 1}',
            })
            continue
        seen_payment_ids[payment_id] = idx

        account = account_lookup.get(customer_ref.casefold())
        if not account:
            result_rows.append({
                'payment_id': payment_id,
                'status': 'error',
                'error': f'unknown customer: {customer_ref}',
            })
            continue

        try:
            amount_cents = _parse_amount_cents(amount_str)
        except DomainError:
            result_rows.append({
                'payment_id': payment_id,
                'status': 'error',
                'error': f'invalid amount: {amount_str}',
            })
            continue

        open_invoices = sorted(
            [inv for inv in store.invoices if inv.account_id == account.id and inv.status == 'open'],
            key=lambda inv: (inv.due_date, inv.id),
        )

        allocations: list[dict] = []
        remaining = amount_cents
        for inv in open_invoices:
            if remaining <= 0:
                break
            available = invoice_remaining[inv.id]
            if available <= 0:
                continue
            applied = min(remaining, available)
            invoice_remaining[inv.id] -= applied
            remaining -= applied
            allocations.append({
                'invoice_id': inv.id,
                'applied_cents': applied,
                'remaining_after_cents': invoice_remaining[inv.id],
            })

        credit_remainder_cents = remaining
        affected_accounts[account.id] = account
        account_credit_additions[account.id] = (
            account_credit_additions.get(account.id, 0) + credit_remainder_cents
        )

        result_rows.append({
            'payment_id': payment_id,
            'status': 'valid',
            'account_id': account.id,
            'allocations': allocations,
            'credit_remainder_cents': credit_remainder_cents,
        })

    account_revisions = {aid: acct.revision for aid, acct in affected_accounts.items()}
    preview_id = f'prev_{uuid.uuid4().hex[:12]}'

    store.previews[preview_id] = {
        'preview_id': preview_id,
        'rows': result_rows,
        'account_revisions': account_revisions,
        '_invoice_remaining': invoice_remaining,
        '_affected_account_ids': list(affected_accounts.keys()),
        '_account_credit_additions': account_credit_additions,
    }

    return {
        'preview_id': preview_id,
        'rows': result_rows,
        'account_revisions': account_revisions,
    }


def commit_preview(store: Store, preview_id: str) -> dict:
    plan = store.previews.get(preview_id)
    if not plan:
        raise DomainError('preview not found', 'preview_not_found', 404)

    if preview_id in store.committed_preview_ids:
        accounts = [a for a in store.accounts if a.id in plan['_affected_account_ids']]
        return {'status': 'already_committed', 'accounts': [a.to_dict() for a in accounts]}

    with store.lock:
        if preview_id in store.committed_preview_ids:
            accounts = [a for a in store.accounts if a.id in plan['_affected_account_ids']]
            return {'status': 'already_committed', 'accounts': [a.to_dict() for a in accounts]}

        for account_id, expected_revision in plan['account_revisions'].items():
            account = next((a for a in store.accounts if a.id == account_id), None)
            if account is None or account.revision != expected_revision:
                raise DomainError(
                    f'account {account_id} has changed since preview',
                    'stale_preview',
                    409,
                )

        new_remaining = plan['_invoice_remaining']
        for inv in store.invoices:
            if new_remaining.get(inv.id, inv.remaining_cents) != inv.remaining_cents:
                inv.remaining_cents = new_remaining[inv.id]
                if inv.remaining_cents == 0:
                    inv.status = 'paid'

        credit_additions = plan['_account_credit_additions']
        for account in store.accounts:
            if account.id in plan['_affected_account_ids']:
                account.credit_cents += credit_additions.get(account.id, 0)
                account.revision += 1

        store.committed_preview_ids.add(preview_id)

        accounts = [a for a in store.accounts if a.id in plan['_affected_account_ids']]
        return {'status': 'committed', 'accounts': [a.to_dict() for a in accounts]}
