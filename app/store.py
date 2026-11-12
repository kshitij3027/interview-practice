"""SQLite-backed contract directory and note editing."""
import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'fixtures' / 'catalog.json'
DB = ROOT / 'data' / 'cycleledger.sqlite'

class DomainError(Exception):
    def __init__(self, status, message, current=None):
        super().__init__(message)
        self.status = status
        self.current = current

@contextmanager
def connect(path=DB):
    connection = sqlite3.connect(str(path), timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize(path=DB, catalog=CATALOG):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = json.loads(Path(catalog).read_text())
    with connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS contracts (id TEXT PRIMARY KEY, org_id TEXT NOT NULL, customer TEXT NOT NULL, plan_id TEXT NOT NULL, status TEXT NOT NULL, seats INTEGER NOT NULL, period_start TEXT NOT NULL, period_end TEXT NOT NULL, revision INTEGER NOT NULL, note TEXT NOT NULL, changes_json TEXT NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS contracts_org ON contracts(org_id, customer, id)')
        db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        if not db.execute('SELECT 1 FROM metadata WHERE key=?', ('seeded',)).fetchone():
            db.executemany('INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?,?,?,?)', [
                (v['id'], v['orgId'], v['customer'], v['planId'], v['status'], v['seats'], v['periodStart'], v['periodEnd'], v['revision'], v['note'], json.dumps(v['changes'])) for v in seed['contracts']
            ])
            db.execute('INSERT INTO metadata VALUES (?,?)', ('seeded', '1'))
    return path

def catalog():
    seed = json.loads(CATALOG.read_text())
    return {'organizations': seed['organizations'], 'plans': seed['plans']}

def as_contract(row, plan_lookup):
    contract = {'id': row['id'], 'orgId': row['org_id'], 'customer': row['customer'], 'planId': row['plan_id'], 'status': row['status'], 'seats': row['seats'], 'periodStart': row['period_start'], 'periodEnd': row['period_end'], 'revision': row['revision'], 'note': row['note'], 'changes': json.loads(row['changes_json'])}
    contract['plan'] = plan_lookup[row['plan_id']]
    return contract

def plans():
    return {p['id']: p for p in catalog()['plans']}

def require_org(org):
    if org not in {o['id'] for o in catalog()['organizations']}:
        raise DomainError(400, 'Unknown organization')

def list_contracts(org, q='', status='', offset=0, limit=30, path=DB):
    require_org(org)
    if not isinstance(q, str) or not isinstance(status, str):
        raise DomainError(400, 'Invalid filter')
    if status not in ('', 'active', 'paused', 'ended') or not (0 <= offset <= 1000000 and 1 <= limit <= 100):
        raise DomainError(400, 'Invalid pagination or status')
    where = 'org_id=? AND lower(customer || " " || id) LIKE ?'
    args = [org, '%' + q.strip().lower().replace('%', '\\%').replace('_', '\\_') + '%']
    where = where.replace('LIKE ?', "LIKE ? ESCAPE '\\'")
    if status:
        where += ' AND status=?'
        args.append(status)
    with connect(path) as db:
        total = db.execute('SELECT count(*) FROM contracts WHERE ' + where, args).fetchone()[0]
        rows = db.execute('SELECT * FROM contracts WHERE ' + where + ' ORDER BY customer COLLATE NOCASE, id LIMIT ? OFFSET ?', [*args, limit, offset]).fetchall()
    plan_lookup = plans()
    return {'total': total, 'contracts': [as_contract(r, plan_lookup) for r in rows]}

def get_contract(contract_id, org, path=DB):
    require_org(org)
    with connect(path) as db:
        row = db.execute('SELECT * FROM contracts WHERE id=? AND org_id=?', (contract_id, org)).fetchone()
    if not row:
        raise DomainError(404, 'Contract not found')
    return as_contract(row, plans())

def edit_note(contract_id, org, expected_revision, note, path=DB):
    require_org(org)
    if type(expected_revision) is not int or not isinstance(note, str) or len(note) > 2000:
        raise DomainError(400, 'Invalid note or revision')
    cleaned = note.strip()
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM contracts WHERE id=? AND org_id=?', (contract_id, org)).fetchone()
        if not row:
            raise DomainError(404, 'Contract not found')
        current = as_contract(row, plans())
        if row['revision'] != expected_revision:
            raise DomainError(409, 'Contract changed. Reload before saving.', current)
        if row['note'] != cleaned:
            db.execute('UPDATE contracts SET note=?, revision=revision+1 WHERE id=? AND org_id=?', (cleaned, contract_id, org))
        row = db.execute('SELECT * FROM contracts WHERE id=? AND org_id=?', (contract_id, org)).fetchone()
    return as_contract(row, plans())
