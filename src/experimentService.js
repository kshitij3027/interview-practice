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

  setExclusion(userId, excluded, reason) {
    const result = excluded ? this.store.excludeUser(userId, reason) : this.store.includeUser(userId);
    if (!result.ok) return result;
    return { ok: true, revision: result.revision, user_id: userId, excluded };
  }
}
