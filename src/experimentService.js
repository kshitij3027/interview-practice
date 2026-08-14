import { computeFunnel, EXPERIMENT, FUNNEL_STEPS, SEGMENTS } from './funnel.js';

export class ExperimentService {
  constructor(store) { this.store = store; }

  overview() {
    const assignments = this.store.listAssignments();
    const events = this.store.listEvents();
    const byVariant = {};
    for (const assignment of assignments) {
      const bucket = byVariant[assignment.variant] ??= { assigned: 0, excluded: 0 };
      bucket.assigned += 1;
      if (assignment.excluded) bucket.excluded += 1;
    }
    return { experiment: 'checkout-copy', revision: this.store.revision, assignment_count: assignments.length, raw_event_count: events.length, variants: byVariant };
  }

  users() { return { revision: this.store.revision, users: this.store.listAssignments() }; }

  // Computed from a single store snapshot, so `revision` always describes the exact dataset
  // these numbers came from. The client relies on that stamp to detect stale responses, and
  // `segment` is echoed back so it can also discard a response for a segment it no longer has
  // selected. `steps` carries the canonical funnel order so the UI need not restate it.
  funnel({ segment = 'all' } = {}) {
    const requested = segment ?? 'all';
    if (!SEGMENTS.includes(requested)) return { ok: false, code: 'invalid_segment' };
    const snapshot = this.store.snapshot();
    const report = computeFunnel({ assignments: snapshot.assignments, events: snapshot.events, segment: requested });
    return {
      ok: true,
      experiment: EXPERIMENT,
      revision: snapshot.revision,
      segment: requested,
      steps: [...FUNNEL_STEPS], // copied: never hand out the shared module constant

      eligible_total: report.eligible_total,
      variants: report.variants
    };
  }

  setExclusion(userId, excluded, reason) {
    const result = excluded ? this.store.excludeUser(userId, reason) : this.store.includeUser(userId);
    if (!result.ok) return result;
    return { ok: true, revision: result.revision, user_id: userId, excluded };
  }
}
