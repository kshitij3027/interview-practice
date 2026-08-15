export function parseCohortsCsv(text) {
  return text
    .split(/\r?\n/)
    .filter(line => line.trim())
    .slice(1)
    .map(line => {
      const [cohortId, label, plan, region, minEmployees] = line.split(',').map(cell => cell.trim());
      return {
        cohortId,
        label,
        plan: plan || null,
        region: region || null,
        minEmployees: minEmployees === '' ? 0 : Number(minEmployees)
      };
    });
}

export function matchesCohort(account, cohort) {
  return (cohort.plan === null || account.plan === cohort.plan) &&
    (cohort.region === null || account.region === cohort.region) &&
    account.employees >= cohort.minEmployees;
}

export function bucketFor(flagKey, cohortId, accountId) {
  const key = `${flagKey}:${cohortId}:${accountId}`;
  let h = 0x811c9dc5;
  for (let i = 0; i < key.length; i++) {
    h ^= key.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h % 100;
}

export function normalizeExcludeIds(input) {
  if (!input) return [];
  const seen = new Set();
  const ids = [];
  for (const value of input) {
    const id = value.trim();
    if (id && !seen.has(id)) {
      seen.add(id);
      ids.push(id);
    }
  }
  return ids;
}

export function calculateRollout({ accounts, flag, cohort, percentage, excludeIds }) {
  const ids = normalizeExcludeIds(excludeIds);
  const excludeSet = new Set(ids);
  const accountIds = new Set(accounts.map(account => account.id));
  const unknownExclusions = ids.filter(id => !accountIds.has(id));
  const overrides = flag.overrides || {};
  const buckets = {
    selected: [],
    eligibleNotSelected: [],
    explicitlyOverridden: [],
    excluded: []
  };

  function toEntry(account) {
    const hasOverride = Object.prototype.hasOwnProperty.call(overrides, account.id);
    return {
      id: account.id,
      name: account.name,
      plan: account.plan,
      region: account.region,
      employees: account.employees,
      bucket: bucketFor(flag.key, cohort.cohortId, account.id),
      hasOverride,
      override: hasOverride ? overrides[account.id] : null,
      excluded: excludeSet.has(account.id)
    };
  }

  for (const account of accounts) {
    if (!matchesCohort(account, cohort)) continue;
    const entry = toEntry(account);
    if (entry.hasOverride) buckets.explicitlyOverridden.push(entry);
    if (entry.excluded) buckets.excluded.push(entry);
    if (!entry.hasOverride && !entry.excluded) {
      buckets[entry.bucket < percentage ? 'selected' : 'eligibleNotSelected'].push(entry);
    }
  }

  for (const bucket of Object.values(buckets)) bucket.sort((a, b) => a.id.localeCompare(b.id));

  return {
    basedOnRevision: flag.revision,
    selected: buckets.selected,
    eligibleNotSelected: buckets.eligibleNotSelected,
    explicitlyOverridden: buckets.explicitlyOverridden,
    excluded: buckets.excluded,
    unknownExclusions
  };
}
