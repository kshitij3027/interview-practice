import { normalizeExcludeIds } from './rollout.js';

function toInteger(value) {
  if (typeof value === 'number') return Number.isInteger(value) ? value : null;
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value);
    return Number.isInteger(n) ? n : null;
  }
  return null;
}

function validateInputs(input) {
  const cohortId = input?.cohortId;
  if (typeof cohortId !== 'string' || !cohortId.trim()) return { error: 'cohort_id_required' };

  const percentage = toInteger(input?.percentage);
  if (percentage === null || percentage < 0 || percentage > 100) return { error: 'percentage_invalid' };

  const rawExcludeIds = input?.excludeIds ?? [];
  if (!Array.isArray(rawExcludeIds) || rawExcludeIds.some(id => typeof id !== 'string')) {
    return { error: 'exclude_ids_invalid' };
  }

  return {
    value: {
      cohortId: cohortId.trim(),
      percentage,
      excludeIds: normalizeExcludeIds(rawExcludeIds)
    }
  };
}

export function listCohorts(store) {
  return { status: 200, body: { cohorts: store.listCohorts() } };
}

export function previewRollout(store, input) {
  const validated = validateInputs(input);
  if (validated.error) return { status: 400, body: { error: validated.error } };

  const result = store.calculateRollout(validated.value);
  if (result.error === 'cohort_not_found') return { status: 404, body: { error: result.error } };
  if (result.error) return { status: 400, body: { error: result.error } };

  return {
    status: 200,
    body: {
      ...result,
      inputSnapshot: structuredClone(validated.value)
    }
  };
}

export function applyRollout(store, input) {
  const validated = validateInputs(input);
  if (validated.error) return { status: 400, body: { error: validated.error } };

  const requestId = input?.requestId;
  if (typeof requestId !== 'string' || !requestId.trim()) {
    return { status: 400, body: { error: 'request_id_required' } };
  }

  const expectedRevision = toInteger(input?.expectedRevision);
  if (expectedRevision === null || expectedRevision < 1) {
    return { status: 400, body: { error: 'expected_revision_required' } };
  }

  const result = store.applyRollout({
    ...validated.value,
    requestId: requestId.trim(),
    expectedRevision
  });

  if (result.error === 'stale') {
    return { status: 409, body: { error: 'stale', currentRevision: result.currentRevision } };
  }
  if (result.error === 'request_id_conflict') return { status: 409, body: { error: result.error } };
  if (result.error === 'cohort_not_found') return { status: 404, body: { error: result.error } };
  if (result.error) return { status: 400, body: { error: result.error } };
  return { status: 200, body: result };
}
