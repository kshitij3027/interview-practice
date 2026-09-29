import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(root, 'fixtures', name), 'utf8'));
}

function readJsonl(name) {
  return fs.readFileSync(path.join(root, 'fixtures', name), 'utf8')
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line, index) => {
      try { return JSON.parse(line); }
      catch { throw new Error(name + ':' + (index + 1) + ' is not valid JSON'); }
    });
}

function assertUnique(items, key, label) {
  const seen = new Set();
  for (const item of items) {
    const value = item[key];
    if (typeof value !== 'string' || !value) throw new Error(label + ' has invalid ' + key);
    if (seen.has(value)) throw new Error(label + ' has duplicate ' + key + ': ' + value);
    seen.add(value);
  }
}

export function loadFixtures() {
  const suites = readJson('suites.json');
  const runs = readJson('runs.json');
  const cases = readJson('cases.json');
  const observations = readJsonl('observations.jsonl');

  assertUnique(suites, 'id', 'suite');
  assertUnique(runs, 'id', 'run');
  assertUnique(cases, 'id', 'case');
  assertUnique(observations, 'observationId', 'observation');

  const suiteById = new Map(suites.map(s => [s.id, s]));
  const runById = new Map(runs.map(r => [r.id, r]));
  const caseById = new Map(cases.map(c => [c.suiteId + ':' + c.id, c]));

  for (const suite of suites) {
    const baseline = runById.get(suite.approvedRunId);
    if (!baseline || baseline.suiteId !== suite.id) throw new Error('suite ' + suite.id + ' has invalid approvedRunId');
  }

  for (const run of runs) {
    if (!suiteById.has(run.suiteId)) throw new Error('run ' + run.id + ' references unknown suite');
  }

  for (const item of cases) {
    if (!suiteById.has(item.suiteId)) throw new Error('case ' + item.id + ' references unknown suite');
    if (!Number.isInteger(item.weight) || item.weight <= 0) throw new Error('case ' + item.id + ' has invalid weight');
  }

  for (const obs of observations) {
    const run = runById.get(obs.runId);
    if (!run || run.suiteId !== obs.suiteId) throw new Error('observation ' + obs.observationId + ' has invalid run');
    if (!caseById.has(obs.suiteId + ':' + obs.caseId)) throw new Error('observation ' + obs.observationId + ' has invalid case');
    if (!Number.isInteger(obs.attempt) || obs.attempt < 1) throw new Error('observation ' + obs.observationId + ' has invalid attempt');
    if (!['ok', 'error'].includes(obs.status)) throw new Error('observation ' + obs.observationId + ' has invalid status');
    if (Number.isNaN(Date.parse(obs.recordedAt))) throw new Error('observation ' + obs.observationId + ' has invalid recordedAt');
  }

  return { suites, runs, cases, observations };
}
