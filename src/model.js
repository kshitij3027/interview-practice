export function clone(value) {
  return structuredClone(value);
}

export function normalizeNote(value) {
  if (typeof value !== 'string') throw new Error('note must be a string');
  const note = value.trim();
  if (note.length > 240) throw new Error('note must be at most 240 characters');
  return note;
}

export function orderedSuites(suites) {
  return [...suites].sort((a, b) =>
    a.owner.localeCompare(b.owner) || a.name.localeCompare(b.name) || a.id.localeCompare(b.id)
  );
}

export function matchesSuiteFilters(suite, { owner = '', status = '' } = {}) {
  if (owner && suite.owner !== owner) return false;
  if (status && suite.status !== status) return false;
  return true;
}
