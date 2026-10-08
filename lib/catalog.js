import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const SOURCE = fileURLToPath(new URL('../fixtures/bins.json', import.meta.url));
export function loadBins(file = SOURCE) {
  const bins = JSON.parse(readFileSync(file, 'utf8'));
  if (!Array.isArray(bins) || bins.length < 1) throw Error('Expected bin records');
  const ids = new Set();
  for (const bin of bins) {
    if (!bin.id || ids.has(bin.id) || !bin.sku || !bin.zone || !['active','locked'].includes(bin.status) || typeof bin.note !== 'string') throw Error('Invalid bin');
    ids.add(bin.id);
    if (![bin.onHand,bin.caseSize,bin.revision].every(Number.isSafeInteger) || bin.onHand < 0 || bin.caseSize < 1 || bin.revision < 1) throw Error('Invalid count or revision');
  }
  return structuredClone(bins);
}
export function noteValue(input) { if (typeof input !== 'string') throw Error('Note must be text'); const value = input.trim(); if (value.length > 200) throw Error('Note exceeds 200 characters'); return value; }
