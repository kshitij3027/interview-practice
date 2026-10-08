import test from 'node:test';
import assert from 'node:assert/strict';
import { loadFixtures } from '../server/data.js';
test('fixture validation and representative unreliable readings',()=>{
  const {shipments,readings}=loadFixtures();
  assert.equal(shipments.length,6);
  assert.equal(readings.length,27);
  assert.ok(readings.some(r=>r.quality==='bad'));
  assert.ok(readings.filter(r=>r.sampleId==='sm-33').length>=2);
});
