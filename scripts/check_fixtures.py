from pathlib import Path
import csv
import json

root = Path(__file__).resolve().parents[1]
workspace = json.loads((root / 'fixtures/workspace.json').read_text())
assert len(workspace['lots']) == 12
assert len({row['id'] for row in workspace['lots']}) == 12
assert len(workspace['plants']) == 3
assert len(workspace['specifications']) == 3
assert all(row['product'] in {s['product'] for s in workspace['specifications']} for row in workspace['lots'])
with (root / 'fixtures/instrument_export.csv').open(newline='', encoding='utf-8-sig') as handle:
    rows = list(csv.DictReader(handle))
assert len(rows) >= 15
assert len({r['event_id'] for r in rows}) < len(rows)
assert all(r['lot_id'] and r['sample_id'] for r in rows)
print(f'Fixture check passed: {len(workspace["lots"])} lots, {len(workspace["samples"])} seeded samples, {len(rows)} instrument rows')
