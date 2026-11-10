import { readFileSync } from 'node:fs';

const copy = value => structuredClone(value);
export class DomainError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code; }
}

export function createStore(seed = JSON.parse(readFileSync(new URL('../fixtures/workspace.json', import.meta.url), 'utf8'))) {
  return {
    organizations: copy(seed.organizations),
    customers: copy(seed.customers),
    flags: copy(seed.flags),
    datasetRevision: 1
  };
}

function organizationExists(store, orgId) {
  return store.organizations.some(org => org.id === orgId);
}

export function listOrganizations(store) { return copy(store.organizations); }
export function listCustomers(store, orgId) {
  if (!organizationExists(store, orgId)) throw new DomainError(404, 'NOT_FOUND', 'Organization not found');
  return copy(store.customers.filter(customer => customer.orgId === orgId).sort((a,b) => a.id.localeCompare(b.id)));
}
export function listFlags(store, {orgId, search = '', status = 'all', limit = 50} = {}) {
  if (!organizationExists(store, orgId)) throw new DomainError(404, 'NOT_FOUND', 'Organization not found');
  if (typeof search !== 'string' || !['all','enabled','disabled'].includes(status) || !Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new DomainError(400, 'INVALID_QUERY', 'Invalid filter');
  }
  const term = search.trim().toLocaleLowerCase('en-US');
  const selected = store.flags.filter(flag => flag.orgId === orgId &&
    flag.name.toLocaleLowerCase('en-US').includes(term) &&
    (status === 'all' || flag.enabled === (status === 'enabled')))
    .sort((a,b) => a.id.localeCompare(b.id));
  return { total: selected.length, datasetRevision: store.datasetRevision,
    flags: copy(selected.slice(0, limit).map(({id, orgId, name, enabled, revision, note}) => ({id, orgId, name, enabled, revision, note}))) };
}
export function getFlag(store, orgId, flagId) {
  const flag = store.flags.find(item => item.id === flagId && item.orgId === orgId);
  if (!flag || !organizationExists(store, orgId)) throw new DomainError(404, 'NOT_FOUND', 'Flag not found');
  return copy(flag);
}
export function editNote(store, orgId, flagId, body) {
  const flag = store.flags.find(item => item.id === flagId && item.orgId === orgId);
  if (!flag) throw new DomainError(404, 'NOT_FOUND', 'Flag not found');
  if (!body || typeof body.note !== 'string' || body.note.trim().length > 500 || !Number.isSafeInteger(body.expectedRevision) || body.expectedRevision < 0) {
    throw new DomainError(400, 'INVALID_NOTE', 'Expected a note and revision');
  }
  if (body.expectedRevision !== flag.revision) throw new DomainError(409, 'STALE_REVISION', 'Flag changed; refresh and retry');
  const note = body.note.trim();
  if (note !== flag.note) { flag.note = note; flag.revision++; store.datasetRevision++; }
  return getFlag(store, orgId, flagId);
}
