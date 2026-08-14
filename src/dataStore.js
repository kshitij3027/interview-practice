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
