export const state = {
  accounts: [],
  flag: null,
  datasetRevision: 0,
  filter: 'all',
  busy: null,
  error: '',
  rollout: {
    cohorts: [],
    form: { cohortId: '', percentage: '', excludeText: '' },
    preview: null,
    seq: 0,
    busy: null,
    conflict: '',
    error: '',
    applied: null
  }
};

export function visibleAccounts() {
  return state.accounts.filter(a => state.filter === 'all' || a.plan === state.filter);
}

export function normalizeExcludeText(text) {
  const seen = new Set();
  const ids = [];
  for (const value of String(text ?? '').split(',')) {
    const id = value.trim();
    if (id && !seen.has(id)) {
      seen.add(id);
      ids.push(id);
    }
  }
  return ids;
}

export function normalizeRolloutForm(form) {
  const cohortId = String(form?.cohortId ?? '').trim();
  if (!cohortId) return null;

  const rawPercentage = form?.percentage;
  if (typeof rawPercentage !== 'string' && typeof rawPercentage !== 'number') return null;
  if (typeof rawPercentage === 'string' && rawPercentage.trim() === '') return null;
  const percentage = Number(rawPercentage);
  if (!Number.isInteger(percentage) || percentage < 0 || percentage > 100) return null;

  return {
    cohortId,
    percentage,
    excludeIds: normalizeExcludeText(form?.excludeText)
  };
}

export function sameInputs(a, b) {
  if (!a || !b) return false;
  return a.cohortId === b.cohortId &&
    a.percentage === b.percentage &&
    a.excludeIds.length === b.excludeIds.length &&
    a.excludeIds.every((id, i) => id === b.excludeIds[i]);
}

export function isPreviewStale(currentState) {
  return Boolean(currentState.rollout.preview && currentState.rollout.preview.basedOnRevision !== currentState.flag?.revision);
}

export function isPreviewDiverged(currentState) {
  return Boolean(
    currentState.rollout.preview &&
    !sameInputs(normalizeRolloutForm(currentState.rollout.form), currentState.rollout.preview.inputSnapshot)
  );
}

export function canApply(currentState) {
  return Boolean(
    currentState.rollout.preview &&
    !currentState.rollout.busy &&
    !isPreviewStale(currentState) &&
    !isPreviewDiverged(currentState)
  );
}
