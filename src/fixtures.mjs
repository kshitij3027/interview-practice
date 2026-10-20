import { readFileSync } from 'node:fs';
const root = new URL('../', import.meta.url);
export function loadFixtures() {
  const cases = JSON.parse(readFileSync(new URL('fixtures/cases.json', root), 'utf8')).cases;
  const events = readFileSync(new URL('fixtures/activity.jsonl', root), 'utf8')
    .split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
  return { cases, events };
}
export const copy = value => structuredClone(value);
