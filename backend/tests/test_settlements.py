"""
Seed state (reset before each test via conftest autouse):

Accounts:
  acct_1  ACME-001   credit=0     revision=7
  acct_2  BRIGHT-44  credit=1250  revision=3
  acct_3  CLOUD-9    credit=0     revision=11

Invoices (open unless noted):
  inv_100  acct_1  due=2026-07-01  remaining=9000
  inv_101  acct_1  due=2026-07-15  remaining=5000
  inv_200  acct_2  due=2026-06-20  remaining=2500
  inv_201  acct_2  due=2026-08-01  remaining=4000
  inv_300  acct_3  due=2026-07-10  remaining=0     PAID
  inv_301  acct_3  due=2026-08-05  remaining=8000
"""

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def preview(client, csv_text):
    return client.post('/api/settlements/preview', json={'csv_text': csv_text})


def commit(client, preview_id):
    return client.post('/api/settlements/commit', json={'preview_id': preview_id})


def make_csv(*rows, header='payment_id,customer_ref,amount,received_at,note'):
    lines = [header] + list(rows)
    return '\n'.join(lines) + '\n'


def get_invoice(client, account_id, invoice_id):
    return next(
        i for i in client.get(f'/api/accounts/{account_id}').json()['invoices']
        if i['id'] == invoice_id
    )


def get_account(client, account_id):
    return client.get(f'/api/accounts/{account_id}').json()['account']


# ---------------------------------------------------------------------------
# Preview — structure
# ---------------------------------------------------------------------------

def test_preview_returns_preview_id_rows_and_revisions(client):
    csv = make_csv('PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,wire')
    r = preview(client, csv)
    assert r.status_code == 200
    body = r.json()
    assert body['preview_id'].startswith('prev_')
    assert len(body['rows']) == 1
    assert 'account_revisions' in body


# ---------------------------------------------------------------------------
# Preview — valid row allocation
# ---------------------------------------------------------------------------

def test_preview_valid_row_allocates_to_earliest_invoice_first(client):
    csv = make_csv('PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,wire')
    row = preview(client, csv).json()['rows'][0]
    assert row['status'] == 'valid'
    assert row['account_id'] == 'acct_1'
    # inv_100 (due 2026-07-01) before inv_101 (due 2026-07-15)
    assert row['allocations'][0]['invoice_id'] == 'inv_100'
    assert row['allocations'][0]['applied_cents'] == 7500
    assert row['allocations'][0]['remaining_after_cents'] == 1500
    assert row['credit_remainder_cents'] == 0


def test_preview_partial_invoice_payment(client):
    csv = make_csv('PAY-001,ACME-001,50.00,2026-08-13T10:00:00Z,partial')
    row = preview(client, csv).json()['rows'][0]
    assert row['allocations'][0]['invoice_id'] == 'inv_100'
    assert row['allocations'][0]['applied_cents'] == 5000
    assert row['allocations'][0]['remaining_after_cents'] == 4000
    assert row['credit_remainder_cents'] == 0


def test_preview_overpayment_remainder_goes_to_credit(client):
    # acct_1 open total = 9000 + 5000 = 14000; pay 15000 → 1000 credit
    csv = make_csv('PAY-001,ACME-001,150.00,2026-08-13T10:00:00Z,over')
    row = preview(client, csv).json()['rows'][0]
    assert row['status'] == 'valid'
    assert len(row['allocations']) == 2
    assert row['credit_remainder_cents'] == 1000


def test_preview_payment_spanning_two_invoices(client):
    # acct_2: inv_200 remaining=2500, inv_201 remaining=4000; pay 60.00=6000
    csv = make_csv('PAY-001,BRIGHT-44,60.00,2026-08-13T10:00:00Z,span')
    row = preview(client, csv).json()['rows'][0]
    allocs = {a['invoice_id']: a for a in row['allocations']}
    assert allocs['inv_200']['applied_cents'] == 2500
    assert allocs['inv_200']['remaining_after_cents'] == 0
    assert allocs['inv_201']['applied_cents'] == 3500
    assert allocs['inv_201']['remaining_after_cents'] == 500
    assert row['credit_remainder_cents'] == 0


def test_preview_skips_paid_invoices(client):
    # acct_3: inv_300 is paid; only inv_301 (8000) is open
    csv = make_csv('PAY-001,CLOUD-9,45.00,2026-08-13T10:00:00Z,test')
    row = preview(client, csv).json()['rows'][0]
    assert all(a['invoice_id'] != 'inv_300' for a in row['allocations'])
    assert row['allocations'][0]['invoice_id'] == 'inv_301'


def test_preview_snapshots_account_revision(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    body = preview(client, csv).json()
    assert body['account_revisions']['acct_1'] == 7


# ---------------------------------------------------------------------------
# Preview — row-level errors
# ---------------------------------------------------------------------------

def test_preview_unknown_customer_is_row_error_others_continue(client):
    csv = make_csv(
        'PAY-001,UNKNOWN-77,10.00,2026-08-13T10:00:00Z,bad',
        'PAY-002,ACME-001,10.00,2026-08-13T10:00:00Z,good',
    )
    rows = preview(client, csv).json()['rows']
    assert rows[0]['status'] == 'error'
    assert 'unknown customer' in rows[0]['error'].lower()
    assert rows[1]['status'] == 'valid'


def test_preview_malformed_amount_is_row_error_others_continue(client):
    csv = make_csv(
        'PAY-001,ACME-001,not-a-number,2026-08-13T10:00:00Z,bad',
        'PAY-002,ACME-001,10.00,2026-08-13T10:00:00Z,good',
    )
    rows = preview(client, csv).json()['rows']
    assert rows[0]['status'] == 'error'
    assert rows[1]['status'] == 'valid'


def test_preview_zero_amount_is_row_error(client):
    csv = make_csv('PAY-001,ACME-001,0.00,2026-08-13T10:00:00Z,zero')
    assert preview(client, csv).json()['rows'][0]['status'] == 'error'


def test_preview_negative_amount_is_row_error(client):
    csv = make_csv('PAY-001,ACME-001,-10.00,2026-08-13T10:00:00Z,neg')
    assert preview(client, csv).json()['rows'][0]['status'] == 'error'


# ---------------------------------------------------------------------------
# Preview — duplicates
# ---------------------------------------------------------------------------

def test_preview_duplicate_payment_id_flags_later_occurrence(client):
    csv = make_csv(
        'PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,first',
        'PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,dup',
    )
    rows = preview(client, csv).json()['rows']
    assert rows[0]['status'] == 'valid'
    assert rows[1]['status'] == 'duplicate'


def test_preview_duplicate_not_double_counted(client):
    # Two identical PAY-001 rows; only first should allocate 7500 to inv_100
    csv = make_csv(
        'PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,first',
        'PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,dup',
    )
    rows = preview(client, csv).json()['rows']
    assert rows[0]['allocations'][0]['remaining_after_cents'] == 1500  # 9000 - 7500


def test_preview_sequential_payments_same_account_share_invoice_state(client):
    # PAY-001 pays 75.00 → inv_100 remaining 1500; PAY-002 sees that residual
    csv = make_csv(
        'PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,first',
        'PAY-002,ACME-001,80.00,2026-08-13T10:00:00Z,second',
    )
    rows = preview(client, csv).json()['rows']
    # PAY-002 should see inv_100 with 1500 remaining, then inv_101 with 5000
    second_allocs = {a['invoice_id']: a for a in rows[1]['allocations']}
    assert second_allocs['inv_100']['applied_cents'] == 1500
    assert second_allocs['inv_100']['remaining_after_cents'] == 0
    assert second_allocs['inv_101']['applied_cents'] == 5000
    assert second_allocs['inv_101']['remaining_after_cents'] == 0
    assert rows[1]['credit_remainder_cents'] == 1500  # 8000 - 1500 - 5000


# ---------------------------------------------------------------------------
# Preview — CSV format
# ---------------------------------------------------------------------------

def test_preview_customer_ref_case_insensitive_and_trimmed(client):
    csv = make_csv('PAY-001, acme-001 ,10.00,2026-08-13T10:00:00Z,test')
    assert preview(client, csv).json()['rows'][0]['status'] == 'valid'


def test_preview_column_order_independent(client):
    csv = make_csv(
        'wire,75.00,PAY-001,2026-08-13T10:00:00Z,ACME-001',
        header='note,amount,payment_id,received_at,customer_ref',
    )
    assert preview(client, csv).json()['rows'][0]['status'] == 'valid'


def test_preview_empty_trailing_lines_ignored(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test') + '\n\n'
    assert len(preview(client, csv).json()['rows']) == 1


def test_preview_missing_required_column_returns_400(client):
    csv = 'payment_id,customer_ref,amount\nPAY-001,ACME-001,10.00\n'
    assert preview(client, csv).status_code == 400


# ---------------------------------------------------------------------------
# Preview — does not mutate state
# ---------------------------------------------------------------------------

def test_preview_does_not_mutate_invoices_accounts_or_revisions(client):
    csv = make_csv('PAY-001,ACME-001,150.00,2026-08-13T10:00:00Z,over')
    preview(client, csv)

    acct = get_account(client, 'acct_1')
    assert acct['revision'] == 7
    assert acct['credit_cents'] == 0

    inv = get_invoice(client, 'acct_1', 'inv_100')
    assert inv['remaining_cents'] == 9000
    assert inv['status'] == 'open'


# ---------------------------------------------------------------------------
# Commit — happy path
# ---------------------------------------------------------------------------

def test_commit_returns_committed_status(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    r = commit(client, pid)
    assert r.status_code == 200
    assert r.json()['status'] == 'committed'


def test_commit_updates_invoice_remaining(client):
    csv = make_csv('PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,wire')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    inv = get_invoice(client, 'acct_1', 'inv_100')
    assert inv['remaining_cents'] == 1500
    assert inv['status'] == 'open'


def test_commit_marks_invoice_paid_when_fully_paid(client):
    # inv_200 has remaining=2500; pay exactly 25.00
    csv = make_csv('PAY-001,BRIGHT-44,25.00,2026-08-13T10:00:00Z,payoff')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    inv = get_invoice(client, 'acct_2', 'inv_200')
    assert inv['remaining_cents'] == 0
    assert inv['status'] == 'paid'


def test_commit_adds_credit_remainder_to_account(client):
    # acct_1 open=14000; pay 15000 → 1000 credit; acct_1 credit starts at 0
    csv = make_csv('PAY-001,ACME-001,150.00,2026-08-13T10:00:00Z,over')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    assert get_account(client, 'acct_1')['credit_cents'] == 1000


def test_commit_increments_account_revision_exactly_once(client):
    # Two valid rows for acct_1 → revision must go 7 → 8 (not 9)
    csv = make_csv(
        'PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,first',
        'PAY-002,ACME-001,10.00,2026-08-13T10:00:00Z,second',
    )
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    assert get_account(client, 'acct_1')['revision'] == 8


def test_commit_only_affects_accounts_with_valid_rows(client):
    # Only acct_1 touched; acct_2 revision must be unchanged
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    assert get_account(client, 'acct_2')['revision'] == 3


# ---------------------------------------------------------------------------
# Commit — stale preview (race condition / optimistic concurrency)
# ---------------------------------------------------------------------------

def test_commit_stale_returns_409(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    # Intervening manual credit bumps acct_1 revision
    client.post('/api/accounts/acct_1/credits', json={'amountCents': 100, 'reason': 'adj'})
    r = commit(client, pid)
    assert r.status_code == 409
    assert r.json()['detail']['code'] == 'stale_preview'


def test_commit_stale_is_atomic_no_partial_apply(client):
    # Preview touches acct_1 and acct_2; only acct_1 goes stale
    csv = make_csv(
        'PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,first',
        'PAY-002,BRIGHT-44,10.00,2026-08-13T10:00:00Z,second',
    )
    pid = preview(client, csv).json()['preview_id']
    client.post('/api/accounts/acct_1/credits', json={'amountCents': 100, 'reason': 'adj'})

    r = commit(client, pid)
    assert r.status_code == 409
    # acct_2 must be untouched
    assert get_account(client, 'acct_2')['revision'] == 3
    assert get_invoice(client, 'acct_2', 'inv_200')['remaining_cents'] == 2500


# ---------------------------------------------------------------------------
# Commit — idempotency (retry safety)
# ---------------------------------------------------------------------------

def test_commit_idempotent_returns_already_committed(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    r = commit(client, pid)
    assert r.status_code == 200
    assert r.json()['status'] == 'already_committed'


def test_commit_idempotent_does_not_double_apply(client):
    csv = make_csv('PAY-001,ACME-001,75.00,2026-08-13T10:00:00Z,wire')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    commit(client, pid)  # retry
    # revision must still be 8, not 9
    assert get_account(client, 'acct_1')['revision'] == 8
    assert get_invoice(client, 'acct_1', 'inv_100')['remaining_cents'] == 1500


# ---------------------------------------------------------------------------
# Commit — unknown preview id
# ---------------------------------------------------------------------------

def test_commit_unknown_preview_id_returns_404(client):
    r = commit(client, 'prev_doesnotexist')
    assert r.status_code == 404
    assert r.json()['detail']['code'] == 'preview_not_found'


# ---------------------------------------------------------------------------
# Existing behavior is unaffected
# ---------------------------------------------------------------------------

def test_manual_credit_still_works_after_settlement_commit(client):
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    commit(client, pid)
    r = client.post('/api/accounts/acct_1/credits', json={'amountCents': 500, 'reason': 'adj'})
    assert r.status_code == 200
    # settlement: 7→8, manual credit: 8→9
    assert r.json()['account']['revision'] == 9


def test_manual_credit_between_preview_and_commit_invalidates_commit(client):
    # Verifies manual credit participates in revision tracking
    csv = make_csv('PAY-001,ACME-001,10.00,2026-08-13T10:00:00Z,test')
    pid = preview(client, csv).json()['preview_id']
    client.post('/api/accounts/acct_1/credits', json={'amountCents': 100, 'reason': 'adj'})
    assert commit(client, pid).status_code == 409
