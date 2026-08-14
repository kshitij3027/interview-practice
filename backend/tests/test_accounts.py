def test_lists_accounts(client):
    response = client.get('/api/accounts')
    assert response.status_code == 200
    assert [a['external_id'] for a in response.json()] == ['ACME-001', 'BRIGHT-44', 'CLOUD-9']


def test_get_account_includes_only_its_invoices(client):
    response = client.get('/api/accounts/acct_1')
    assert response.status_code == 200
    body = response.json()
    assert body['account']['name'] == 'Acme North'
    assert {i['id'] for i in body['invoices']} == {'inv_100', 'inv_101'}


def test_missing_account_returns_structured_error(client):
    response = client.get('/api/accounts/missing')
    assert response.status_code == 404
    assert response.json()['detail']['code'] == 'account_not_found'
