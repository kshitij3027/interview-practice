def test_manual_credit_updates_balance_and_revision(client):
    response = client.post('/api/accounts/acct_2/credits', json={
        'amountCents': 500,
        'reason': 'courtesy adjustment',
    })
    assert response.status_code == 200
    account = response.json()['account']
    assert account['credit_cents'] == 1750
    assert account['revision'] == 4


def test_manual_credit_rejects_invalid_input(client):
    response = client.post('/api/accounts/acct_2/credits', json={'amountCents': 0, 'reason': 'x'})
    assert response.status_code == 400
    assert response.json()['detail']['code'] == 'invalid_amount'
