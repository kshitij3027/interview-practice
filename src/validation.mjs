export function fail(status, code, message) {
  const error = new Error(message);
  error.status = status;
  error.code = code;
  throw error;
}

export function delayValue(value) {
  if (value === undefined || value === null || value === '') return 0;
  const n = Number(value);
  if (!Number.isSafeInteger(n) || n < 0 || n > 1200) fail(400, 'invalid_delay', 'delayMs must be an integer from 0 to 1200');
  return n;
}

export function noteValue(value) {
  if (typeof value !== 'string') fail(400, 'invalid_note', 'note must be a string');
  const note = value.trim();
  if (note.length > 240) fail(400, 'invalid_note', 'note is too long');
  return note;
}

export function expectedRevision(value) {
  if (!Number.isSafeInteger(value) || value < 0) fail(400, 'invalid_revision', 'expectedRevision must be a nonnegative safe integer');
  return value;
}

export function compactSearch(value) {
  return String(value ?? '').normalize('NFKC').trim().toLocaleLowerCase('en-US');
}
