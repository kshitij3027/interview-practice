import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export function fixturePath(name) { return path.join(root, 'fixtures', name); }
export function readWorkspace() { return JSON.parse(fs.readFileSync(fixturePath('workspace.json'), 'utf8')); }
export function readJsonl(name) {
  return fs.readFileSync(fixturePath(name), 'utf8').split(/\r?\n/).filter(Boolean).map((line, index) => {
    try { return JSON.parse(line); } catch { throw new Error(`${name}:${index + 1}: invalid JSON`); }
  });
}
