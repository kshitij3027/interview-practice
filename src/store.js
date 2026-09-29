import { clone, matchesSuiteFilters, normalizeNote, orderedSuites } from './model.js';

export class SuiteStore {
  constructor(fixtures) {
    this.suites = new Map(fixtures.suites.map(s => [s.id, clone(s)]));
    this.runs = clone(fixtures.runs);
    this.cases = clone(fixtures.cases);
    this.observations = clone(fixtures.observations);
    this.datasetRevision = 11;
  }

  listSuites(filters = {}) {
    return orderedSuites([...this.suites.values()].filter(s => matchesSuiteFilters(s, filters))).map(clone);
  }

  getSuite(id) {
    const suite = this.suites.get(id);
    if (!suite) return null;
    const runs = this.runs
      .filter(r => r.suiteId === id)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt) || a.id.localeCompare(b.id));
    return { ...clone(suite), availableRuns: clone(runs), datasetRevision: this.datasetRevision };
  }

  updateNote(id, { note, expectedRevision }) {
    const suite = this.suites.get(id);
    if (!suite) return { status: 404, body: { error: 'suite_not_found' } };
    if (!Number.isInteger(expectedRevision)) return { status: 400, body: { error: 'expectedRevision must be an integer' } };
    if (suite.revision !== expectedRevision) {
      return { status: 409, body: { error: 'stale_revision', suite: this.getSuite(id) } };
    }

    let normalized;
    try { normalized = normalizeNote(note); }
    catch (error) { return { status: 400, body: { error: error.message } }; }

    if (normalized === suite.note) {
      return { status: 200, body: { changed: false, suite: this.getSuite(id) } };
    }

    suite.note = normalized;
    suite.revision += 1;
    this.datasetRevision += 1;
    return { status: 200, body: { changed: true, suite: this.getSuite(id) } };
  }
}
