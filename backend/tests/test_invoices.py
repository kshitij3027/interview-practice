def test_lists_invoices_with_current_remaining_amounts(client):
    response = client.get('/api/invoices')
    assert response.status_code == 200
    invoices = {i['id']: i for i in response.json()}
    assert invoices['inv_200']['remaining_cents'] == 2500
    assert invoices['inv_300']['status'] == 'paid'
