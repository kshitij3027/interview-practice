#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node --input-type=module <<'JS'
import { loadFixture, createStore } from './src/domain.js';
import assert from 'node:assert/strict';
const fixture = loadFixture();
assert.equal(new Set(fixture.employees.map(x=>x.id)).size, fixture.employees.length);
assert.equal(new Set(fixture.shifts.map(x=>x.id)).size, fixture.shifts.length);
for(const shift of fixture.shifts) {
  assert.ok(fixture.employees.some(x=>x.id===shift.employeeId));
  assert.ok(Date.parse(shift.endAt)>Date.parse(shift.startAt));
  assert.ok(shift.breaks.every(b=>Date.parse(b.endAt)>Date.parse(b.startAt)));
}
assert.equal(createStore().listShifts().shifts.length, fixture.shifts.length);
console.log(`Fixture validation passed: ${fixture.employees.length} employees / ${fixture.shifts.length} shifts`);
JS
