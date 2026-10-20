import { loadFixtures, copy } from './fixtures.mjs';
import { ApiError, bad, notFound } from './errors.mjs';

export function makeStore(data = loadFixtures()) {
  const cases = new Map(data.cases.map(c => [c.id, copy(c)]));
  const events = data.events.map(copy);
  let datasetRevision = 1;
  const orderedActivity = id => events.filter(e => e.caseId === id).sort((a,b) => Date.parse(a.at)-Date.parse(b.at) || a.eventId.localeCompare(b.eventId)).map(copy);
  return {
    list({tenant = 'all',status = 'all',q = ''} = {}) {
      const search = q.trim().toLocaleLowerCase('en');
      const items = [...cases.values()]
        .filter(c => tenant === 'all' || c.tenantId === tenant)
        .filter(c => status === 'all' || c.status === status)
        .filter(c => !search || [c.id,c.customerId,c.subject,c.issueKey].some(v => v.toLocaleLowerCase('en').includes(search)))
        .sort((a,b) => Date.parse(b.updatedAt)-Date.parse(a.updatedAt) || a.id.localeCompare(b.id)).map(copy);
      return {items,datasetRevision};
    },
    get(id) {
      const item = cases.get(id); if (!item) throw notFound();
      return {case:copy(item),activity:orderedActivity(id),datasetRevision};
    },
    updateNote(id,{note,expectedRevision}) {
      const item = cases.get(id); if (!item) throw notFound();
      if (typeof note !== 'string' || note.trim().length > 300) throw bad('invalid_note','Note must contain at most 300 characters');
      if (!Number.isSafeInteger(expectedRevision) || expectedRevision < 0) throw bad('invalid_revision','Expected revision must be a nonnegative integer');
      if (item.revision !== expectedRevision) throw new ApiError(409,'stale_revision','Case changed since it was read',{currentRevision:item.revision});
      const normalized = note.trim();
      const changed = item.note !== normalized;
      if (changed) { item.note=normalized; item.revision++; datasetRevision++; }
      return {changed,...this.get(id)};
    }
  };
}
