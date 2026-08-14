// Funnel semantics for the fixed three-step funnel
// product_viewed -> checkout_started -> order_completed.
//
// The backend is the source of truth for these rules. Three of them are subtle enough to
// spell out, because the telemetry fixture is intentionally messy:
//
// 1. Duplicate event_ids. Only one occurrence of a repeated event_id may influence the
//    report. The winner is the occurrence that sorts first by (occurred_at, stable JSON of
//    the payload). File position is deliberately NOT a tiebreak: a "first row wins" rule
//    would make the winner depend on JSONL order as soon as two duplicates disagree, and
//    results must be identical under any permutation of the input.
//
// 2. The 24h window is anchored on the user's FIRST qualifying product_viewed. Later
//    product_viewed events do not re-anchor or reset it.
//
// 3. Step selection is greedy-earliest, and that is optimal rather than merely convenient.
//    The anchor t1 is fixed by rule 2, so picking the smallest valid checkout_started
//    maximally relaxes the constraint on order_completed, and the smallest valid
//    order_completed is the one most likely to land inside the window. If the earliest
//    valid completion misses the window, every later one misses it too — there is nothing
//    to backtrack to.

export const FUNNEL_STEPS = ['product_viewed', 'checkout_started', 'order_completed'];
export const FUNNEL_WINDOW_MS = 24 * 60 * 60 * 1000; // inclusive upper bound
export const SEGMENTS = ['all', 'self-serve', 'enterprise'];
export const EXPERIMENT = 'checkout-copy';

function toMs(value) {
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms;
}

// JSON with recursively sorted object keys, so two payloads that differ only in key order
// serialize identically and the duplicate tiebreak stays content-derived.
function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map(key => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value) ?? 'null';
}

// Unparseable timestamps sort last so a well-formed duplicate always wins over a broken one.
function duplicateRank(event) {
  const ms = toMs(event.occurred_at);
  return ms === null ? Number.POSITIVE_INFINITY : ms;
}

export function dedupeEvents(events) {
  const winners = new Map();
  for (const event of events) {
    const key = String(event.event_id);
    const current = winners.get(key);
    if (current === undefined) {
      winners.set(key, event);
      continue;
    }
    // Compared, not subtracted: two unparseable timestamps both rank Infinity, and
    // Infinity - Infinity is NaN, which would silently skip the payload tiebreak and let
    // file order decide the winner.
    const rank = duplicateRank(event);
    const currentRank = duplicateRank(current);
    if (rank < currentRank || (rank === currentRank && stableStringify(event) < stableStringify(current))) {
      winners.set(key, event);
    }
  }
  return [...winners.values()];
}

// `sortedEvents` must be this user's qualifying events sorted by (occurred_at, event_id).
// Returns how many funnel steps the user reached: 0, 1, 2 or 3.
export function userPathSteps(sortedEvents) {
  const firstAtOrAfter = (name, floor) => {
    for (const event of sortedEvents) {
      if (event.name === name && (floor === null || event.occurredAtMs >= floor)) return event.occurredAtMs;
    }
    return null;
  };

  const t1 = firstAtOrAfter('product_viewed', null);
  if (t1 === null) return 0;

  const t2 = firstAtOrAfter('checkout_started', t1);
  if (t2 === null) return 1;

  const deadline = t1 + FUNNEL_WINDOW_MS;
  const t3 = firstAtOrAfter('order_completed', t2);
  if (t3 === null || t3 > deadline) return 2;

  return 3;
}

// Percentages use the immediately preceding step as denominator. A zero denominator yields
// null rather than NaN/Infinity. Rounding is half-up to one decimal, applied identically to
// every rate.
export function rate(numerator, denominator) {
  if (!denominator) return null;
  return Math.round((numerator / denominator) * 1000) / 10;
}

export function computeFunnel({ assignments = [], events = [], segment = 'all' } = {}) {
  const eligible = new Map();
  const variantNames = new Set();

  for (const assignment of assignments) {
    if (assignment.experiment !== EXPERIMENT) continue;
    variantNames.add(assignment.variant);
    if (assignment.excluded) continue;
    if (segment !== 'all' && assignment.segment !== segment) continue;
    const assignedAtMs = toMs(assignment.assigned_at);
    if (assignedAtMs === null) continue;
    eligible.set(assignment.user_id, { variant: assignment.variant, assignedAtMs });
  }

  const byUser = new Map();
  for (const event of dedupeEvents(events)) {
    if (!FUNNEL_STEPS.includes(event.name)) continue;
    const assignment = eligible.get(event.user_id);
    if (!assignment) continue;
    const occurredAtMs = toMs(event.occurred_at);
    if (occurredAtMs === null || occurredAtMs < assignment.assignedAtMs) continue;
    const bucket = byUser.get(event.user_id) ?? [];
    bucket.push({ name: event.name, event_id: String(event.event_id), occurredAtMs });
    byUser.set(event.user_id, bucket);
  }

  const variants = {};
  for (const name of [...variantNames].sort()) {
    variants[name] = { eligible: 0, steps: { product_viewed: 0, checkout_started: 0, order_completed: 0 } };
  }

  for (const [userId, assignment] of eligible) {
    const bucket = variants[assignment.variant];
    bucket.eligible += 1;
    const userEvents = (byUser.get(userId) ?? []).sort((a, b) =>
      a.occurredAtMs - b.occurredAtMs || (a.event_id < b.event_id ? -1 : a.event_id > b.event_id ? 1 : 0));
    const reached = userPathSteps(userEvents);
    for (let step = 0; step < reached; step += 1) bucket.steps[FUNNEL_STEPS[step]] += 1;
  }

  for (const bucket of Object.values(variants)) {
    bucket.rates = {
      product_viewed: rate(bucket.steps.product_viewed, bucket.eligible),
      checkout_started: rate(bucket.steps.checkout_started, bucket.steps.product_viewed),
      order_completed: rate(bucket.steps.order_completed, bucket.steps.checkout_started)
    };
  }

  return { segment, eligible_total: eligible.size, variants };
}
