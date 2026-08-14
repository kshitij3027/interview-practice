import test from 'node:test';
import assert from 'node:assert/strict';
import { loadFixtureData } from '../src/dataStore.js';
import { computeFunnel, dedupeEvents, rate, userPathSteps, FUNNEL_WINDOW_MS } from '../src/funnel.js';

const HOUR = 60 * 60 * 1000;
const T0 = Date.parse('2026-08-10T09:00:00Z');
const iso = ms => new Date(ms).toISOString();

function assigned(userId, variant, segment = 'self-serve', assignedAtMs = T0, extra = {}) {
  return { user_id: userId, experiment: 'checkout-copy', variant, segment, assigned_at: iso(assignedAtMs), ...extra };
}

let eventCounter = 0;
function event(userId, name, atMs, extra = {}) {
  eventCounter += 1;
  return { event_id: `t-${eventCounter}`, user_id: userId, name, occurred_at: iso(atMs), ...extra };
}

// Steps reached by a single user, given their own raw events.
function stepsFor(events, assignedAtMs = T0) {
  const result = computeFunnel({ assignments: [assigned('u-1', 'control', 'self-serve', assignedAtMs)], events });
  return result.variants.control.steps;
}

function reached(events, assignedAtMs = T0) {
  const steps = stepsFor(events, assignedAtMs);
  return steps.product_viewed + steps.checkout_started + steps.order_completed;
}

// Deterministic linear-congruential shuffle: no Math.random, so failures reproduce.
function shuffle(items, seed) {
  const copy = [...items];
  let state = seed;
  for (let i = copy.length - 1; i > 0; i -= 1) {
    state = (state * 1103515245 + 12345) % 2147483648;
    const j = state % (i + 1);
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

// --- fixture-driven oracle -------------------------------------------------

test('funnel over the fixture matches the hand-derived oracle', () => {
  const { assignments, events } = loadFixtureData();
  assert.deepEqual(computeFunnel({ assignments, events, segment: 'all' }), {
    segment: 'all',
    eligible_total: 8,
    variants: {
      control: {
        eligible: 4,
        steps: { product_viewed: 4, checkout_started: 4, order_completed: 2 },
        rates: { product_viewed: 100, checkout_started: 100, order_completed: 50 }
      },
      treatment: {
        eligible: 4,
        steps: { product_viewed: 4, checkout_started: 4, order_completed: 3 },
        rates: { product_viewed: 100, checkout_started: 100, order_completed: 75 }
      }
    }
  });
});

test('segment filtering narrows eligibility and step counts', () => {
  const { assignments, events } = loadFixtureData();

  const selfServe = computeFunnel({ assignments, events, segment: 'self-serve' });
  assert.equal(selfServe.eligible_total, 4);
  assert.deepEqual(selfServe.variants.control.steps, { product_viewed: 2, checkout_started: 2, order_completed: 1 });
  assert.deepEqual(selfServe.variants.treatment.steps, { product_viewed: 2, checkout_started: 2, order_completed: 1 });

  const enterprise = computeFunnel({ assignments, events, segment: 'enterprise' });
  assert.equal(enterprise.eligible_total, 4);
  assert.deepEqual(enterprise.variants.control.steps, { product_viewed: 2, checkout_started: 2, order_completed: 1 });
  assert.deepEqual(enterprise.variants.treatment.steps, { product_viewed: 2, checkout_started: 2, order_completed: 2 });
  assert.equal(enterprise.variants.treatment.rates.order_completed, 100);
});

test('excluded users leave both the eligible count and every step count', () => {
  const { assignments, events } = loadFixtureData();
  const withExclusion = assignments.map(a => (a.user_id === 'u-102' ? { ...a, excluded: true } : a));
  const result = computeFunnel({ assignments: withExclusion, events, segment: 'all' });
  assert.equal(result.eligible_total, 7);
  assert.equal(result.variants.treatment.eligible, 3);
  assert.deepEqual(result.variants.treatment.steps, { product_viewed: 3, checkout_started: 3, order_completed: 2 });
});

test('events for users not assigned to the experiment are ignored', () => {
  const { assignments, events } = loadFixtureData();
  assert.ok(events.some(e => e.user_id === 'u-999'));
  const withoutStranger = events.filter(e => e.user_id !== 'u-999');
  assert.deepEqual(
    computeFunnel({ assignments, events, segment: 'all' }),
    computeFunnel({ assignments, events: withoutStranger, segment: 'all' })
  );
});

test('step counts never increase further down the funnel', () => {
  const { assignments, events } = loadFixtureData();
  for (const segment of ['all', 'self-serve', 'enterprise']) {
    for (const [name, variant] of Object.entries(computeFunnel({ assignments, events, segment }).variants)) {
      const { product_viewed: s1, checkout_started: s2, order_completed: s3 } = variant.steps;
      assert.ok(variant.eligible >= s1 && s1 >= s2 && s2 >= s3, `${segment}/${name} funnel is not monotonic`);
    }
  }
});

// --- determinism (results must not depend on file order) -------------------

test('duplicate event_ids with differing timestamps resolve identically in any order', () => {
  const assignments = [assigned('u-1', 'control')];
  const rows = [
    event('u-1', 'product_viewed', T0),
    event('u-1', 'checkout_started', T0 + HOUR),
    { event_id: 'd-1', user_id: 'u-1', name: 'order_completed', occurred_at: iso(T0 + 2 * HOUR) },
    { event_id: 'd-1', user_id: 'u-1', name: 'order_completed', occurred_at: iso(T0 + 30 * HOUR) }
  ];
  // The earlier occurrence wins, so the completion lands inside the 24h window.
  assert.equal(reached(rows), 3);
  assert.equal(reached([...rows].reverse()), 3);
  assert.equal(dedupeEvents(rows).find(e => e.event_id === 'd-1').occurred_at, iso(T0 + 2 * HOUR));
  assert.equal(dedupeEvents([...rows].reverse()).find(e => e.event_id === 'd-1').occurred_at, iso(T0 + 2 * HOUR));
});

test('duplicate event_ids differing only in payload resolve identically in any order', () => {
  const rows = [
    { event_id: 'd-2', user_id: 'u-1', name: 'order_completed', occurred_at: iso(T0), source: 'beta' },
    { event_id: 'd-2', user_id: 'u-1', name: 'order_completed', occurred_at: iso(T0), source: 'alpha' }
  ];
  assert.equal(dedupeEvents(rows)[0].source, 'alpha');
  assert.equal(dedupeEvents([...rows].reverse())[0].source, 'alpha');
});

test('duplicates with unparseable timestamps still resolve by payload, not file order', () => {
  const rows = [
    { event_id: 'd-3', user_id: 'u-1', name: 'order_completed', occurred_at: 'not-a-date', source: 'beta' },
    { event_id: 'd-3', user_id: 'u-1', name: 'order_completed', occurred_at: 'also-broken', source: 'alpha' }
  ];
  assert.equal(dedupeEvents(rows)[0].source, 'alpha');
  assert.equal(dedupeEvents([...rows].reverse())[0].source, 'alpha');
});

test('shuffling the fixture event order does not change the report', () => {
  const { assignments, events } = loadFixtureData();
  const baseline = computeFunnel({ assignments, events, segment: 'all' });
  for (const seed of [1, 7, 42, 1337, 90210]) {
    assert.deepEqual(computeFunnel({ assignments, events: shuffle(events, seed), segment: 'all' }), baseline);
    assert.deepEqual(computeFunnel({ assignments: shuffle(assignments, seed), events, segment: 'all' }), baseline);
  }
});

test('events sharing a timestamp resolve by event_id, independent of input order', () => {
  const sameTime = iso(T0 + HOUR);
  const rows = [
    { event_id: 'b', user_id: 'u-1', name: 'checkout_started', occurred_at: sameTime },
    { event_id: 'a', user_id: 'u-1', name: 'product_viewed', occurred_at: sameTime }
  ];
  assert.equal(reached(rows), 2);
  assert.equal(reached([...rows].reverse()), 2);
});

// --- 24 hour window --------------------------------------------------------

test('a completion exactly 24h after the anchor counts, one millisecond later does not', () => {
  const path = at => [
    event('u-1', 'product_viewed', T0),
    event('u-1', 'checkout_started', T0 + HOUR),
    event('u-1', 'order_completed', at)
  ];
  assert.equal(reached(path(T0 + FUNNEL_WINDOW_MS)), 3);
  assert.equal(reached(path(T0 + FUNNEL_WINDOW_MS + 1)), 2);
});

test('a later product_viewed does not re-anchor the 24h window', () => {
  const withCompletionAt = at => [
    event('u-1', 'product_viewed', T0),
    event('u-1', 'product_viewed', T0 + 20 * HOUR),
    event('u-1', 'checkout_started', T0 + 21 * HOUR),
    event('u-1', 'order_completed', at)
  ];
  // 23h after the first view: inside the window.
  assert.equal(reached(withCompletionAt(T0 + 23 * HOUR)), 3);
  // 25h after the first view — within 24h of the *second* view, but the anchor never moved.
  assert.equal(reached(withCompletionAt(T0 + 25 * HOUR)), 2);
});

// --- ordering and repeated steps -------------------------------------------

test('a completion that precedes the checkout does not count as step 3', () => {
  const rows = [
    event('u-1', 'order_completed', T0 + HOUR),
    event('u-1', 'product_viewed', T0 + 2 * HOUR),
    event('u-1', 'checkout_started', T0 + 3 * HOUR)
  ];
  assert.equal(reached(rows), 2);
  assert.equal(reached([...rows].reverse()), 2);
});

test('a repeated step is used when the earlier occurrence cannot form an ordered path', () => {
  const rows = [
    event('u-1', 'checkout_started', T0 + HOUR),      // before the view: unusable
    event('u-1', 'product_viewed', T0 + 2 * HOUR),
    event('u-1', 'checkout_started', T0 + 3 * HOUR)   // the occurrence that qualifies
  ];
  assert.equal(reached(rows), 2);
});

test('userPathSteps selects by time rather than array position', () => {
  const path = [
    { name: 'product_viewed', event_id: 'z', occurredAtMs: T0 },
    { name: 'checkout_started', event_id: 'a', occurredAtMs: T0 },
    { name: 'order_completed', event_id: 'm', occurredAtMs: T0 }
  ];
  assert.equal(userPathSteps(path), 3);
  assert.equal(userPathSteps([]), 0);
});

// --- eligibility -----------------------------------------------------------

test('an event exactly at assigned_at qualifies, one millisecond earlier does not', () => {
  assert.equal(reached([event('u-1', 'product_viewed', T0)]), 1);
  assert.equal(reached([event('u-1', 'product_viewed', T0 - 1)]), 0);
});

// --- rates -----------------------------------------------------------------

test('zero denominators produce null rather than NaN or Infinity', () => {
  const assignments = [
    { ...assigned('u-1', 'control'), excluded: true },
    { ...assigned('u-2', 'treatment'), excluded: true }
  ];
  const result = computeFunnel({ assignments, events: [event('u-1', 'product_viewed', T0)], segment: 'all' });
  assert.equal(result.eligible_total, 0);
  assert.deepEqual(result.variants.control.rates, { product_viewed: null, checkout_started: null, order_completed: null });
  assert.deepEqual(result.variants.control.steps, { product_viewed: 0, checkout_started: 0, order_completed: 0 });
  // A NaN or Infinity anywhere would serialize to null and fail the round-trip comparison.
  assert.deepEqual(JSON.parse(JSON.stringify(result)), result);
});

test('rates round half-up to one decimal place', () => {
  assert.equal(rate(1, 3), 33.3);
  assert.equal(rate(2, 3), 66.7);
  assert.equal(rate(1, 8), 12.5);
  assert.equal(rate(0, 4), 0);
  assert.equal(rate(3, 0), null);
});

test('a variant with no events still appears with zeroed counts', () => {
  const assignments = [assigned('u-1', 'control'), assigned('u-2', 'treatment')];
  const result = computeFunnel({ assignments, events: [event('u-1', 'product_viewed', T0)], segment: 'all' });
  assert.deepEqual(result.variants.treatment, {
    eligible: 1,
    steps: { product_viewed: 0, checkout_started: 0, order_completed: 0 },
    rates: { product_viewed: 0, checkout_started: null, order_completed: null }
  });
});

// --- purity ----------------------------------------------------------------

test('computeFunnel does not mutate its inputs', () => {
  const { assignments, events } = loadFixtureData();
  const assignmentsBefore = structuredClone(assignments);
  const eventsBefore = structuredClone(events);
  computeFunnel({ assignments, events, segment: 'all' });
  assert.deepEqual(assignments, assignmentsBefore);
  assert.deepEqual(events, eventsBefore);
});
