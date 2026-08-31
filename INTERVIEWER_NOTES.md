# POST-PRACTICE ONLY — RiskPulse Interviewer Notes

Do not expose this file, its contents, or evaluator-only tests to the candidate before the exercise.

## Intended underlying structure

This is primarily a streaming/event-time problem combining:

- a bounded reordering structure keyed by event time;
- per-key sliding-window state;
- incremental frequency accounting for distinct values;
- a small per-partition state machine for idempotent retries and corruption detection.

The candidate-facing problem intentionally avoids naming the data structures. Recognition of the split between global reorder state and merchant-local window state is part of the interview.

## Strong solution approach

A strong deterministic implementation typically keeps:

1. `max_seen_time` and a global priority structure of accepted on-time events keyed by `(occurred_at, event_id)`.
2. For each source partition, the highest seen sequence plus a stable representation of that event's contents. Equal sequence + equal contents is a retry; equal sequence + different contents is corruption; lower sequence is regression.
3. For each merchant, an ordered queue of finalized declines and a `fingerprint -> active count` map, plus `last_alert_time`.
4. Summary counters.

For each unique arrival:

- validate merchant/partition sequencing;
- compute the current watermark from the prior `max_seen_time`;
- reject as late if `occurred_at < watermark`;
- otherwise update `max_seen_time`, insert into the reorder buffer, recompute watermark, and finalize while the smallest buffered timestamp is strictly less than that watermark.

At EOF, drain the entire reorder buffer in `(occurred_at, event_id)` order.

When finalizing an event at `t`, first evict merchant declines with timestamp `< t-window_seconds`. For each expired decline, decrement its fingerprint count and remove zeroes. An approved event stops there. A decline is appended, its fingerprint count incremented, and both thresholds checked. Emit only if the cooldown predicate also passes.

## Complexity target

Let `B` be the number of accepted events currently inside the lateness horizon and `W_m` the active decline count for merchant `m`.

A standard implementation is approximately:

- reorder insertion/removal: `O(log B)` per on-time event;
- merchant-window insert/expiry: amortized `O(1)` per finalized decline, aside from hash-map operations;
- memory: `O(B + sum(W_m) + merchants + partitions)`.

The input should never require sorting all previously seen events or rescanning every decline in a merchant's history.

At the stated skew, Python object overhead can dominate. A candidate does not need to solve memory layout perfectly in one hour, but should recognize that a 20k events/sec hot merchant or a larger lateness budget can make `B` or a single active window large. Compact event representations, sharding, or upstream partition-local watermarks are reasonable production discussion points if semantics permit.

## Why naive approaches fail

- Arrival-order counting gives wrong windows when partitions reorder events.
- Sorting the entire prefix after each arrival is far too expensive.
- Flushing events at `<= watermark` is wrong because an event exactly at the watermark is still allowed to arrive on time.
- Comparing lateness after first advancing the watermark with the arriving event can incorrectly classify edge cases if implemented carelessly.
- Using a set of cards without multiplicity produces wrong distinct counts when one of several declines for the same card expires.
- A global historical event-ID set is not needed for the supplied retry contract and can become an avoidable memory sink.
- Treating equal partition sequence as always a retry misses source corruption.

## Hidden checks

Evaluator tests should include at least these cases:

1. First event when no watermark exists.
2. Event exactly equal to the current watermark is accepted.
3. Event one microsecond/second before the watermark is late and never triggers.
4. Buffered event exactly equal to the watermark is not finalized until watermark advances past it or EOF occurs.
5. Multiple accepted events with identical `occurred_at` finalize by lexicographic `event_id` even when arrival order is reversed.
6. EOF flush produces the final alert(s).
7. Identical retry of current partition sequence increments only `duplicate_retries`.
8. Equal partition sequence with changed merchant, event ID, card, outcome, or timestamp fails.
9. Sequence regression fails even if the payload resembles an older valid event.
10. Window lower-bound equality remains active; one second earlier expires.
11. Distinct-card count remains correct when one of two active declines for the same card expires.
12. Cooldown equality allows a new alert; one second before does not.
13. Approvals advance watermark and can cause older declines to finalize, but never count or alert themselves.
14. Merchant state remains isolated across interleaved merchants.
15. Too-late event does not update merchant state or `processed_events`.
16. UTC normalization makes equivalent offsets compare and output consistently.

## Fixture discoveries expected from the candidate

The candidate should notice without being told the solution:

- arrival order differs from occurrence order across collectors;
- `collector-b` contains an exact retry at sequence 11;
- two merchants have events at the exact same timestamp;
- later events move the watermark enough to make earlier buffered events finalizable;
- a late event is possible once the watermark has advanced substantially;
- merchant thresholds/windows differ, so state cannot be one global counter.

The fixture is representative, not exhaustive. Strong candidates should create their own adversarial cases rather than infer correctness from one sample run.

## Alternative defensible designs

A candidate may batch the entire supplied file and sort it once, but that does not satisfy the streaming/production shape and should lose substantial scaling and event-time credit unless they clearly label it as a prototype and explain the missing path.

A partition-local reorder strategy can be viable only if the candidate can prove it yields the same global event-time ordering and watermark semantics. With the stated single global watermark, a global merge structure is the simpler exact design.

An LLM does not improve the exact ordering/counting core. An LLM could perhaps assist operator explanations downstream, but placing it in the correctness path adds latency/nondeterminism without benefit. A candidate gets full design credit for explicitly rejecting LLM use here.

## Likely AI-agent failure modes

- Implements a generic "sliding window" over arrival timestamps instead of event time.
- Uses `<=` instead of `<` at one of the two watermark boundaries.
- Deduplicates by `event_id` only and fails partition sequence corruption rules.
- Uses a `set` for fingerprints and breaks when repeated cards age out.
- Emits alerts as soon as events arrive rather than when they finalize.
- Checks cooldown using wall clock rather than finalized event time.
- Leaves all processed events in memory.
- Overfits visible fixture output rather than building reusable state transitions.

## Recommended 60-minute prioritization

A strong ordering of work is:

- 0–10 min: inspect fixtures, restate watermark/window/cooldown boundaries, identify invariants;
- 10–25 min: implement partition retry validation and reorder/finalization path;
- 25–40 min: implement merchant-local window accounting and alerts;
- 40–50 min: wire summary/CLI and test same-time/EOF cases;
- 50–60 min: add adversarial boundary tests and prepare complexity/tradeoff walkthrough.

## What to inspect in the walkthrough

Ask the candidate to trace one reordered event through arrival, buffering, watermark movement, finalization, window eviction, and alert decision. Then ask what happens at exact equality for the watermark, window lower bound, and cooldown. Finally ask how memory changes if one merchant spikes to 20k events/sec or allowed lateness grows from 90 seconds to 10 minutes.
