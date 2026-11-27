const validId = x => typeof x === 'string' && /^[A-Za-z0-9_-]{1,48}$/.test(x) && !/[\r\n]/.test(x);
const integer = (x, lo, hi) => Number.isInteger(x) && x >= lo && x <= hi;
const record = x => x !== null && typeof x === 'object' && !Array.isArray(x);
function fail(msg) { throw new Error(msg); }
function put(map, row) {
  if (map.has(row.id) && JSON.stringify(map.get(row.id)) !== JSON.stringify(row)) fail(`conflicting ID: ${row.id}`);
  map.set(row.id, row);
}
export function normalize(raw) {
  if (!record(raw) || !Array.isArray(raw.reviewers) || !Array.isArray(raw.documents)) fail('expected reviewer and document arrays');
  const reviewers = new Map(), documents = new Map();
  for (const r of raw.reviewers) {
    if (!record(r) || !validId(r.id) || !validId(r.queue) || !integer(r.capacity, 0, 300)) fail('invalid reviewer');
    put(reviewers, {id:r.id, queue:r.queue, capacity:r.capacity});
  }
  for (const d of raw.documents) {
    if (!record(d) || !validId(d.id) || !validId(d.queue) || !integer(d.priority, 1, 5) || !Array.isArray(d.eligible)) fail('invalid document');
    for (const id of d.eligible) {
      if (!validId(id) || reviewers.get(id)?.queue !== d.queue) fail(`invalid eligibility: ${d.id}`);
    }
    const eligible = [...new Set(d.eligible)].sort();
    if (eligible.length > 20) fail('too many eligible reviewers');
    put(documents, {id:d.id, queue:d.queue, priority:d.priority, eligible});
  }
  return {reviewers:[...reviewers.values()], documents:[...documents.values()]};
}
