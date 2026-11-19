import { readFileSync } from 'node:fs';
const initial = JSON.parse(readFileSync(new URL('../fixtures/workspace.json', import.meta.url), 'utf8'));
export function makeCatalog() { return structuredClone(initial); }
