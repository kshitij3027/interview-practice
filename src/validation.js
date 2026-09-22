export const STATUSES = new Set(["pending", "approved", "revoked"]);
export const RISKS = new Set(["low", "medium", "high", "critical"]);

export function normalizeNote(value) {
  if (typeof value !== "string") throw new Error("note must be a string");
  const note = value.trim();
  if (note.length > 200) throw new Error("note must be at most 200 characters");
  return note;
}

export function parseLimit(raw, max) {
  if (raw == null || raw === "") return Math.min(4, max);
  const n = Number(raw);
  if (!Number.isInteger(n) || n < 1 || n > max) throw new Error(`limit must be between 1 and ${max}`);
  return n;
}

export function parseDelay(raw) {
  if (raw == null || raw === "") return 0;
  const n = Number(raw);
  if (!Number.isInteger(n) || n < 0 || n > 1500) throw new Error("delay_ms must be an integer from 0 through 1500");
  return n;
}
