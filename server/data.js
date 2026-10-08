import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'fixtures');
export function loadFixtures() {
  const shipments = JSON.parse(readFileSync(join(root, 'shipments.json'), 'utf8'));
  const readings = ['readings.jsonl', 'additional_readings.jsonl'].flatMap(file =>
    readFileSync(join(root, file), 'utf8').trim().split('\n').map(JSON.parse));
  const ids = new Set(shipments.map(s => s.id));
  if (ids.size !== shipments.length) throw Error('duplicate shipment IDs');
  for (const r of readings) {
    if (!ids.has(r.shipmentId) || !r.sampleId || !Number.isFinite(r.tempC) ||
      !Number.isFinite(Date.parse(r.observedAt)) || !Number.isFinite(Date.parse(r.receivedAt)) ||
      !['ok','bad'].includes(r.quality)) throw Error('invalid reading');
  }
  return { shipments, readings };
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const f = loadFixtures();
  console.log('verified ' + f.shipments.length + ' shipments / ' + f.readings.length + ' readings');
}
