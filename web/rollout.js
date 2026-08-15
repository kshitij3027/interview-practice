import { api } from './api.js';
import { canApply, isPreviewDiverged, isPreviewStale, normalizeRolloutForm, state } from './store.js';

const $ = s => document.querySelector(s);
let deps = null;

function controls() {
  return {
    cohortEl: $('#rollout-cohort'),
    pctEl: $('#rollout-percentage'),
    excludeEl: $('#rollout-exclude')
  };
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[ch]);
}

function syncForm() {
  const { cohortEl, pctEl, excludeEl } = controls();
  state.rollout.form = {
    cohortId: cohortEl.value,
    percentage: pctEl.value,
    excludeText: excludeEl.value
  };
}

function accountLine(entry, note = '') {
  const override = entry.hasOverride ? ` override=${esc(entry.override)}` : '';
  const excluded = entry.excluded ? ' excluded' : '';
  return `<li>${esc(entry.id)} ${esc(entry.name)} (${esc(entry.plan)}, ${esc(entry.region)}, bucket ${esc(entry.bucket)})${override}${excluded}${note}</li>`;
}

function group(title, entries, renderEntry = accountLine) {
  const items = entries.length ? entries.map(renderEntry).join('') : '<li>None</li>';
  return `<section class="rollout-group"><h3>${esc(title)} (${entries.length})</h3><ul>${items}</ul></section>`;
}

function renderResults() {
  const { preview, applied } = state.rollout;
  if (!preview) {
    return applied ? `<p class="rollout-applied">Applied to ${esc(applied.count)} accounts. Flag revision is now ${esc(applied.revision)}.</p>` : '';
  }

  const stale = isPreviewStale(state);
  const diverged = isPreviewDiverged(state);
  const hint = stale ? '<p class="rollout-note">Flag changed since this calculation. Recalculate to continue.</p>' :
    diverged ? '<p class="rollout-note">Inputs changed since this calculation. Recalculate to continue.</p>' : '';
  const appliedSummary = applied ? `<p class="rollout-applied">Applied to ${esc(applied.count)} accounts. Flag revision is now ${esc(applied.revision)}.</p>` : '';
  const selectedCount = preview.selected.length;
  return `${appliedSummary}${hint}<p class="rollout-note">Calculated at flag revision ${esc(preview.basedOnRevision)}. The plan filter above does not limit rollout eligibility.</p><div class="rollout-results">${
    group('Selected', preview.selected) +
    group('Eligible not selected', preview.eligibleNotSelected) +
    group('Explicitly overridden', preview.explicitlyOverridden, entry => accountLine(entry, ' authoritative - not changed by rollout')) +
    group('Excluded', preview.excluded) +
    group('Unknown exclusions', preview.unknownExclusions, id => `<li>${esc(id)}</li>`)
  }</div><p class="rollout-note">${canApply(state) ? `Ready to apply to ${esc(selectedCount)} account(s).` : ''}</p>`;
}

async function calculate() {
  if (state.rollout.busy) return;
  syncForm();
  const form = normalizeRolloutForm(state.rollout.form);
  if (!form) {
    state.rollout.error = 'Enter a cohort and an integer percentage from 0 to 100.';
    state.rollout.conflict = '';
    state.rollout.applied = null;
    renderRollout();
    return;
  }

  state.rollout.busy = 'preview';
  state.rollout.conflict = '';
  state.rollout.error = '';
  state.rollout.applied = null;
  deps.render();
  const seq = ++state.rollout.seq;
  try {
    const preview = await api.previewRollout(form.cohortId, form.percentage, form.excludeIds);
    if (seq !== state.rollout.seq) return;
    state.rollout.preview = { ...preview, requestId: crypto.randomUUID() };
  } catch (e) {
    if (seq !== state.rollout.seq) return;
    state.rollout.error = e.message;
  } finally {
    if (seq === state.rollout.seq) {
      state.rollout.busy = null;
      deps.render();
    }
  }
}

async function apply() {
  if (!canApply(state)) return;
  const preview = state.rollout.preview;
  state.rollout.busy = 'apply';
  state.rollout.conflict = '';
  state.rollout.error = '';
  deps.render();
  try {
    const body = await api.applyRollout(preview.inputSnapshot, preview.basedOnRevision, preview.requestId);
    state.rollout.applied = { count: body.appliedAccountIds.length, revision: body.flag.revision };
    await deps.load();
  } catch (e) {
    if (e.status === 409) {
      state.rollout.conflict = e.body?.error === 'request_id_conflict' ?
        'This calculation was already submitted with different inputs. Recalculate to continue.' :
        e.body?.currentRevision ?
          `Another change landed (flag is now revision ${e.body.currentRevision}). Recalculate to continue.` :
          'Another change landed. Recalculate to continue.';
      await deps.load();
    } else {
      state.rollout.error = e.message;
    }
  } finally {
    state.rollout.busy = null;
    deps.render();
  }
}

export function populateCohorts() {
  const select = $('#rollout-cohort');
  if (!select.options.length) {
    select.innerHTML = state.rollout.cohorts.map(c => `<option value="${esc(c.cohortId)}">${esc(c.label)} (${esc(c.cohortId)})</option>`).join('');
  }
  syncForm();
  renderRollout();
}

export function initRollout({ load, render }) {
  deps = { load, render };
  const { cohortEl, pctEl, excludeEl } = controls();
  const sync = () => {
    syncForm();
    renderRollout();
  };
  for (const el of [cohortEl, pctEl, excludeEl]) {
    el.addEventListener('input', sync);
    el.addEventListener('change', sync);
  }
  $('#rollout-calculate').onclick = calculate;
  $('#rollout-apply').onclick = apply;
}

export function renderRollout() {
  $('#rollout-conflict').textContent = state.rollout.conflict;
  $('#rollout-error').textContent = state.rollout.error;
  $('#rollout-results').innerHTML = renderResults();
  $('#rollout-calculate').disabled = Boolean(state.rollout.busy);
  const applyButton = $('#rollout-apply');
  applyButton.disabled = !canApply(state);
  applyButton.textContent = state.rollout.preview ? `Apply to ${state.rollout.preview.selected.length} account(s)` : 'Apply';
}
