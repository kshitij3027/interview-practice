#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node --input-type=module <<'JS'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const seed = JSON.parse(readFileSync('fixtures/catalog.json'));
assert.equal(seed.studios.length, 2);
assert.equal(seed.assets.length, 8);
const ids = new Set(seed.assets.map(a => a.id));
assert.equal(ids.size, seed.assets.length);
for (const a of seed.assets) {
  assert.ok(seed.studios.some(s => s.id === a.studioId));
  assert.ok(Number.isSafeInteger(a.durationMs) && a.durationMs > 0);
  for (const cues of Object.values(a.captions)) {
    for (const cue of cues) assert.ok(cue.startMs >= 0 && cue.endMs <= a.durationMs && cue.startMs < cue.endMs);
  }
}
assert.match(readFileSync('fixtures/partner_captions.vtt', 'utf8'), /^WEBVTT/);
console.log('Fixtures verified: 2 studios, 8 assets, existing localized captions and partner VTT.');
JS
