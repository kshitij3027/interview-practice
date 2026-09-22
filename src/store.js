import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { normalizeNote } from "./validation.js";

const here = path.dirname(fileURLToPath(import.meta.url));

function clone(value) {
  return structuredClone(value);
}

function encodeCursor(index) {
  return Buffer.from(String(index), "utf8").toString("base64url");
}

function decodeCursor(cursor) {
  if (!cursor) return 0;
  const text = Buffer.from(cursor, "base64url").toString("utf8");
  const n = Number(text);
  if (!Number.isInteger(n) || n < 0) throw new Error("invalid cursor");
  return n;
}

export class GrantStore {
  constructor({ grants, cycle }) {
    this.grants = new Map(grants.map((grant) => [grant.id, clone(grant)]));
    this.cycle = clone(cycle);
    this.datasetRevision = 1;
  }

  static fromFixtures() {
    const grants = JSON.parse(fs.readFileSync(path.join(here, "..", "fixtures", "grants.json"), "utf8"));
    const cycle = JSON.parse(fs.readFileSync(path.join(here, "..", "fixtures", "review_cycle.json"), "utf8"));
    return new GrantStore({ grants, cycle });
  }

  meta() {
    const systems = [...new Set([...this.grants.values()].map((g) => g.system))].sort();
    return { cycle: clone(this.cycle), datasetRevision: this.datasetRevision, systems };
  }

  list({ status = "all", system = "all", risk = "all", cursor = null, limit = 4 } = {}) {
    let rows = [...this.grants.values()];
    if (status !== "all") rows = rows.filter((g) => g.status === status);
    if (system !== "all") rows = rows.filter((g) => g.system === system);
    if (risk !== "all") rows = rows.filter((g) => g.risk === risk);
    rows.sort((a, b) => a.system.localeCompare(b.system) || a.principal.localeCompare(b.principal) || a.id.localeCompare(b.id));
    const start = decodeCursor(cursor);
    if (start > rows.length) throw new Error("cursor is outside the current result set");
    const page = rows.slice(start, start + limit).map(clone);
    const nextIndex = start + page.length;
    return {
      items: page,
      nextCursor: nextIndex < rows.length ? encodeCursor(nextIndex) : null,
      total: rows.length,
      datasetRevision: this.datasetRevision,
    };
  }

  get(id) {
    const grant = this.grants.get(id);
    return grant ? clone(grant) : null;
  }

  updateNote(id, expectedRevision, rawNote) {
    const grant = this.grants.get(id);
    if (!grant) return { kind: "not_found" };
    if (!Number.isInteger(expectedRevision)) return { kind: "invalid", message: "expected_revision must be an integer" };
    if (grant.revision !== expectedRevision) return { kind: "stale", grant: clone(grant), datasetRevision: this.datasetRevision };
    let note;
    try {
      note = normalizeNote(rawNote);
    } catch (error) {
      return { kind: "invalid", message: error.message };
    }
    if (note === grant.ownerNote) return { kind: "ok", changed: false, grant: clone(grant), datasetRevision: this.datasetRevision };
    grant.ownerNote = note;
    grant.revision += 1;
    this.datasetRevision += 1;
    return { kind: "ok", changed: true, grant: clone(grant), datasetRevision: this.datasetRevision };
  }
}
