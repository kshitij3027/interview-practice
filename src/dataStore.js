import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

export function loadFixtureData() {
  const assignments = JSON.parse(fs.readFileSync(path.join(root, 'fixtures', 'assignments.json'), 'utf8'));
  const events = fs.readFileSync(path.join(root, 'fixtures', 'experiment_events.jsonl'), 'utf8')
    .split(/\r?\n/)
    .filter(Boolean)
    .map(line => JSON.parse(line));
  return { assignments, events };
}

export class DataStore {
  constructor(seed = loadFixtureData()) {
    this.assignments = structuredClone(seed.assignments);
    this.events = structuredClone(seed.events);
    this.excludedUsers = new Map();
    this.revision = 1;
  }

  listAssignments() {
    return this.assignments.map(a => ({
      ...a,
      excluded: this.excludedUsers.has(a.user_id),
      exclusion_reason: this.excludedUsers.get(a.user_id) ?? null
    }));
  }

  listEvents() { return structuredClone(this.events); }

  // A consistent read of everything a report needs, in one expression.
  //
  // This is a contract guard, not a fix for a live bug: computeFunnel is synchronous and Node
  // is single-threaded, so today nothing can interleave between three separate reads. But a
  // response must be stamped with a revision that provably describes the data in it, and once
  // any part of report assembly gains an `await` (the report route grows a deliberate delay),
  // three separate reads become genuinely torn. Taking them together makes the safe thing the
  // only reasonable thing.
  snapshot() {
    return { assignments: this.listAssignments(), events: this.listEvents(), revision: this.revision };
  }

  excludeUser(userId, reason) {
    const assignment = this.assignments.find(a => a.user_id === userId);
    if (!assignment) return { ok: false, code: 'not_found' };
    const normalized = String(reason ?? '').trim();
    if (!normalized) return { ok: false, code: 'invalid_reason' };
    this.excludedUsers.set(userId, normalized);
    this.revision += 1;
    return { ok: true, revision: this.revision };
  }

  includeUser(userId) {
    if (!this.assignments.some(a => a.user_id === userId)) return { ok: false, code: 'not_found' };
    if (this.excludedUsers.delete(userId)) this.revision += 1;
    return { ok: true, revision: this.revision };
  }
}
