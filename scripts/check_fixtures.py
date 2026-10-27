import json
from datetime import datetime
from pathlib import Path

base = Path(__file__).resolve().parents[1]
space = json.loads((base / 'fixtures/workspace.json').read_text())
credentials = [json.loads(line) for line in (base / 'fixtures/credentials.jsonl').read_text().splitlines() if line.strip()]
assert isinstance(space['datasetRevision'], int) and space['datasetRevision'] >= 0
assert len({s['id'] for s in space['sites']}) == len(space['sites'])
assert len({v['id'] for v in space['vendors']}) == len(space['vendors'])
assert len({v['id'] for v in space['visits']}) == len(space['visits'])
sites = {site['id']: site for site in space['sites']}
vendors = {vendor['id']: vendor for vendor in space['vendors']}
for v in space['visits']:
    assert v['siteId'] in sites and v['vendorId'] in vendors
    assert sites[v['siteId']]['tenantId'] == vendors[v['vendorId']]['tenantId'] == v['tenantId']
    assert datetime.fromisoformat(v['startAt'].replace('Z','+00:00')) < datetime.fromisoformat(v['endAt'].replace('Z','+00:00'))
    assert (v['status'] == 'issued') == (v['issuedPassId'] is not None)
assert all(isinstance(row, dict) for row in credentials)
print(f'Fixture verification passed: {len(sites)} sites; {len(vendors)} vendors; {len(space["visits"])} visits; {len(credentials)} credential records')
