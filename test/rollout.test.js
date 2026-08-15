import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  bucketFor,
  calculateRollout,
  matchesCohort,
  normalizeExcludeIds,
  parseCohortsCsv
} from '../src/rollout.js';

const accounts = JSON.parse(fs.readFileSync(new URL('../fixtures/accounts.json', import.meta.url), 'utf8'));
const cohorts = parseCohortsCsv(fs.readFileSync(new URL('../fixtures/cohorts.csv', import.meta.url), 'utf8'));
const flag = {
  key: 'smart-compose',
  name: 'Smart Compose',
  description: 'AI-assisted response drafting',
  enabled: false,
  revision: 1,
  overrides: { 'acct-102': true }
};

function ids(entries) {
  return entries.map(entry => entry.id);
}

function cohort(id) {
  return cohorts.find(c => c.cohortId === id);
}

test('parses the cohort fixture', () => {
  const parsed = parseCohortsCsv(`cohort_id,label,plan,region,min_employees
c-pro-us,US Pro,pro,us,0
c-large-ent,Large Enterprise,enterprise,,500
c-eu-paid,EU Paid,,eu,1
c-apac,APAC All,,apac,0`);
  assert.equal(parsed.length, 4);
  assert.deepEqual(parsed.find(c => c.cohortId === 'c-large-ent'), {
    cohortId: 'c-large-ent',
    label: 'Large Enterprise',
    plan: 'enterprise',
    region: null,
    minEmployees: 500
  });
});

test('blank plan and region become null', () => {
  const parsed = parseCohortsCsv(`cohort_id,label,plan,region,min_employees
c-eu-paid,EU Paid,,eu,1`);
  assert.deepEqual(parsed[0], {
    cohortId: 'c-eu-paid',
    label: 'EU Paid',
    plan: null,
    region: 'eu',
    minEmployees: 1
  });
});

test('tolerates CRLF and a trailing newline', () => {
  const parsed = parseCohortsCsv('cohort_id,label,plan,region,min_employees\r\nc-one,One,,us,\r\n');
  assert.deepEqual(parsed, [{
    cohortId: 'c-one',
    label: 'One',
    plan: null,
    region: 'us',
    minEmployees: 0
  }]);
});

test('null plan matches any plan', () => {
  assert.equal(matchesCohort({ plan: 'starter', region: 'eu', employees: 1 }, cohort('c-eu-paid')), true);
});

test('null region matches any region', () => {
  assert.equal(matchesCohort({ plan: 'enterprise', region: 'apac', employees: 500 }, cohort('c-large-ent')), true);
});

test('min_employees is inclusive', () => {
  const largeEnterprise = cohort('c-large-ent');
  assert.equal(matchesCohort({ plan: 'enterprise', region: 'us', employees: 499 }, largeEnterprise), false);
  assert.equal(matchesCohort({ plan: 'enterprise', region: 'us', employees: 500 }, largeEnterprise), true);
  assert.equal(matchesCohort({ plan: 'enterprise', region: 'us', employees: 501 }, largeEnterprise), true);
});

test('bucket is stable for the same inputs', () => {
  assert.equal(bucketFor('smart-compose', 'c-pro-us', 'acct-101'), bucketFor('smart-compose', 'c-pro-us', 'acct-101'));
});

test('bucket is in range for every account and cohort', () => {
  for (const account of accounts) {
    for (const c of cohorts) {
      const bucket = bucketFor(flag.key, c.cohortId, account.id);
      assert.equal(Number.isInteger(bucket), true);
      assert.equal(bucket >= 0 && bucket <= 99, true);
    }
  }
});

test('bucket changes with the cohort', () => {
  const buckets = new Set(cohorts.map(c => bucketFor(flag.key, c.cohortId, 'acct-105')));
  assert.notEqual(buckets.size, 1);
});

test('trims, drops blanks and dedupes', () => {
  assert.deepEqual(normalizeExcludeIds([' acct-101 ', '', 'acct-101', 'acct-102', '   ']), ['acct-101', 'acct-102']);
});

test('returns [] for undefined/null', () => {
  assert.deepEqual(normalizeExcludeIds(), []);
  assert.deepEqual(normalizeExcludeIds(null), []);
});

test('selected and eligibleNotSelected exclude overridden and excluded accounts', () => {
  const result = calculateRollout({
    accounts,
    flag,
    cohort: cohort('c-eu-paid'),
    percentage: 100,
    excludeIds: ['acct-106']
  });
  assert.deepEqual(ids(result.selected), []);
  assert.deepEqual(ids(result.eligibleNotSelected), []);
  assert.deepEqual(ids(result.explicitlyOverridden), ['acct-102']);
  assert.deepEqual(ids(result.excluded), ['acct-106']);
});

test('explicitly overridden accounts are reported even when excluded', () => {
  const result = calculateRollout({
    accounts,
    flag,
    cohort: cohort('c-eu-paid'),
    percentage: 50,
    excludeIds: ['acct-102']
  });
  assert.equal(ids(result.explicitlyOverridden).includes('acct-102'), true);
  assert.equal(ids(result.excluded).includes('acct-102'), true);
});

test('every cohort match lands in at least one bucket', () => {
  const c = cohort('c-eu-paid');
  const result = calculateRollout({ accounts, flag, cohort: c, percentage: 50, excludeIds: ['acct-102'] });
  const matches = accounts.filter(account => matchesCohort(account, c)).map(account => account.id).sort();
  const covered = new Set([
    ...ids(result.selected),
    ...ids(result.eligibleNotSelected),
    ...ids(result.explicitlyOverridden),
    ...ids(result.excluded)
  ]);
  assert.deepEqual([...covered].sort(), matches);
  const reported = new Set([...ids(result.explicitlyOverridden), ...ids(result.excluded)]);
  for (const id of [...ids(result.selected), ...ids(result.eligibleNotSelected)]) {
    assert.equal(reported.has(id), false);
  }
});

test('unknown exclusion ids are reported without aborting', () => {
  const result = calculateRollout({
    accounts,
    flag,
    cohort: cohort('c-pro-us'),
    percentage: 100,
    excludeIds: ['acct-999', 'acct-101']
  });
  assert.deepEqual(result.unknownExclusions, ['acct-999']);
  assert.deepEqual(ids(result.excluded), ['acct-101']);
  assert.ok(Array.isArray(result.selected));
});

test('a known account outside the cohort is not reported as unknown', () => {
  const result = calculateRollout({
    accounts,
    flag,
    cohort: cohort('c-pro-us'),
    percentage: 100,
    excludeIds: ['acct-102']
  });
  assert.deepEqual(result.unknownExclusions, []);
});

test('is deterministic across calls and across fresh stores', () => {
  const input = { accounts, flag, cohort: cohort('c-large-ent'), percentage: 35, excludeIds: ['acct-108'] };
  assert.deepEqual(calculateRollout(input), calculateRollout(structuredClone(input)));
});

test('is independent of account order', () => {
  const permutation = [accounts[3], accounts[0], accounts[7], accounts[1], accounts[5], accounts[2], accounts[6], accounts[4]];
  const input = { flag, cohort: cohort('c-large-ent'), percentage: 60, excludeIds: ['acct-108'] };
  assert.deepEqual(
    calculateRollout({ ...input, accounts }),
    calculateRollout({ ...input, accounts: [...accounts].reverse() })
  );
  assert.deepEqual(
    calculateRollout({ ...input, accounts }),
    calculateRollout({ ...input, accounts: permutation })
  );
});

test('is monotonic across percentages', () => {
  for (const c of cohorts) {
    let previous = new Set();
    for (let percentage = 0; percentage <= 100; percentage++) {
      const current = new Set(ids(calculateRollout({ accounts, flag, cohort: c, percentage, excludeIds: [] }).selected));
      for (const id of previous) assert.equal(current.has(id), true);
      previous = current;
    }
  }
});

test('selects nothing at 0 and every eligible account at 100', () => {
  for (const c of cohorts) {
    const atZero = calculateRollout({ accounts, flag, cohort: c, percentage: 0, excludeIds: [] });
    assert.deepEqual(atZero.selected, []);
    const atHundred = calculateRollout({ accounts, flag, cohort: c, percentage: 100, excludeIds: [] });
    assert.deepEqual(atHundred.eligibleNotSelected, []);
  }
});

test('respects a false override', () => {
  const result = calculateRollout({
    accounts,
    flag: { ...flag, overrides: { ...flag.overrides, 'acct-101': false } },
    cohort: cohort('c-pro-us'),
    percentage: 100,
    excludeIds: []
  });
  assert.deepEqual(ids(result.explicitlyOverridden), ['acct-101']);
  assert.deepEqual(ids(result.selected), []);
  assert.equal(result.explicitlyOverridden[0].override, false);
});
