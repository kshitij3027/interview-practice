import fs from 'node:fs';
import { calculateRollout, normalizeExcludeIds, parseCohortsCsv } from './rollout.js';

const accounts = JSON.parse(fs.readFileSync(new URL('../fixtures/accounts.json', import.meta.url), 'utf8'));
const cohorts = parseCohortsCsv(fs.readFileSync(new URL('../fixtures/cohorts.csv', import.meta.url), 'utf8'));
const initialFlag = {
  key: 'smart-compose',
  name: 'Smart Compose',
  description: 'AI-assisted response drafting',
  enabled: false,
  revision: 1,
  overrides: { 'acct-102': true }
};

function fingerprint({ cohortId, percentage, excludeIds, expectedRevision }) {
  return [cohortId, percentage, normalizeExcludeIds(excludeIds).join(','), expectedRevision].join('|');
}

export function createStore() {
  const state = {
    accounts: structuredClone(accounts),
    flag: structuredClone(initialFlag),
    datasetRevision: 1,
    appliedRollouts: {}
  };

  function calc({ cohortId, percentage, excludeIds }) {
    const cohort = cohorts.find(c => c.cohortId === cohortId);
    if (!cohort) return { error: 'cohort_not_found' };
    return calculateRollout({ accounts: state.accounts, flag: state.flag, cohort, percentage, excludeIds });
  }

  return {
    listAccounts() {
      return structuredClone(state.accounts);
    },

    listCohorts() {
      return structuredClone(cohorts);
    },

    getFlag() {
      return structuredClone(state.flag);
    },

    snapshot() {
      return structuredClone(state);
    },

    setOverride(accountId, enabled, expectedRevision) {
      if (!state.accounts.some(a => a.id === accountId)) return { error: 'account_not_found' };
      if (expectedRevision !== state.flag.revision) return { error: 'stale', currentRevision: state.flag.revision };
      state.flag.overrides[accountId] = enabled;
      state.flag.revision++;
      state.datasetRevision++;
      return { flag: structuredClone(state.flag), datasetRevision: state.datasetRevision };
    },

    calculateRollout({ cohortId, percentage, excludeIds }) {
      return calc({ cohortId, percentage, excludeIds });
    },

    applyRollout({ requestId, cohortId, percentage, excludeIds, expectedRevision }) {
      const inputFingerprint = fingerprint({ cohortId, percentage, excludeIds, expectedRevision });
      const prior = state.appliedRollouts[requestId];
      if (prior) {
        if (prior.fingerprint !== inputFingerprint) return { error: 'request_id_conflict' };
        return { ...structuredClone(prior.body), replayed: true };
      }

      if (expectedRevision !== state.flag.revision) {
        return { error: 'stale', currentRevision: state.flag.revision };
      }

      const result = calc({ cohortId, percentage, excludeIds });
      if (result.error) return result;

      const appliedAccountIds = result.selected.map(account => account.id);
      for (const id of appliedAccountIds) state.flag.overrides[id] = true;
      state.flag.revision++;
      state.datasetRevision++;

      const body = {
        appliedAccountIds,
        flag: structuredClone(state.flag),
        datasetRevision: state.datasetRevision,
        replayed: false
      };
      state.appliedRollouts[requestId] = { fingerprint: inputFingerprint, body: structuredClone(body) };
      return structuredClone(body);
    }
  };
}
