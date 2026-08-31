# RiskPulse — One-Hour AI-Assisted Problem-Solving Interview

## Customer context

A payments platform monitors card authorization traffic for sudden merchant-specific decline bursts. Risk operations uses these bursts to decide when to throttle traffic, contact a merchant, or investigate an upstream processor.

The existing detector groups events in file-arrival order. That is producing both false positives and missed alerts because regional collectors buffer and retry events: a record can arrive tens of seconds after a newer authorization from another collector.

You are given representative merchant thresholds and an interleaved authorization stream. Build an in-memory detector that produces deterministic alerts using the event's actual occurrence time while remaining credible at production scale.

## Supplied data

### `fixtures/merchants.csv`

Each merchant has its own policy:

- `merchant_id` — unique merchant identifier
- `window_seconds` — trailing event-time window used for the burst calculation
- `min_declines` — minimum declined authorizations in the active window
- `min_distinct_cards` — minimum distinct card fingerprints among those declines
- `cooldown_seconds` — minimum event-time distance between alerts for that merchant

All numeric policy values are positive integers.

### `fixtures/events.jsonl`

The file is in **arrival order**, not event-time order. Each line contains:

- `event_id` — logical authorization identifier
- `source_partition` — collector partition that produced the event
- `source_seq` — integer sequence assigned by that partition
- `merchant_id`
- `occurred_at` — timezone-aware ISO-8601 timestamp
- `card_fingerprint` — opaque stable card identifier
- `outcome` — `declined` or `approved`

Within a given `source_partition`, `source_seq` values are non-decreasing in arrival order. A collector retry repeats the same sequence and the same logical event. Sequence reuse with different contents is source corruption.

The fixture intentionally contains cross-partition reordering, an identical retry, same-time events, approvals, a watermark boundary case, and an event that arrives too late to affect risk state.

## Goal

Complete `risk_pulse.py` so the CLI consumes the stream once and emits alerts using **event-time semantics**.

The detector has a global allowed-lateness budget of **90 seconds**.

Let `max_seen_time` be the greatest `occurred_at` timestamp among accepted non-retry events seen so far. The current watermark is:

`max_seen_time - 90 seconds`

Before accepting a newly arrived event, compare its `occurred_at` with the current watermark from previously accepted events:

- if `occurred_at < watermark`, the event is too late and must be ignored for risk calculations;
- if `occurred_at == watermark`, it is still on time;
- if there is no watermark yet, the event is on time.

After an on-time event is accepted, update `max_seen_time`, buffer the event, and finalize buffered events whose `occurred_at` is **strictly earlier** than the new watermark. At end-of-file, finalize every remaining buffered event.

Finalized events must be applied in ascending `(occurred_at, event_id)` order, regardless of arrival order.

## Observable requirements

For a finalized event at time `t`, a merchant's active decline window is the closed interval:

`[t - window_seconds, t]`

Only finalized `declined` events count toward the window. `approved` events participate in arrival ordering, watermark advancement, validation, and finalization, but do not count as declines and cannot trigger alerts.

When a finalized declined event is applied:

1. Remove that merchant's older declines that fall before the active-window lower bound.
2. Add the current decline.
3. Compute the active total decline count and active distinct-card count.
4. The event qualifies to trigger an alert only if both configured thresholds are met.
5. If the merchant has already emitted an alert, the current event may emit another only when `t >= last_alert_time + cooldown_seconds`.

For every emitted alert, write exactly one JSON object to stdout:

```json
{
  "type": "alert",
  "merchant_id": "m-100",
  "trigger_event_id": "evt-42",
  "event_time": "2026-08-31T16:05:00Z",
  "window_start": "2026-08-31T16:00:00Z",
  "decline_count": 7,
  "distinct_card_count": 4
}
```

Timestamps in output must be normalized to UTC with a `Z` suffix.

After all input has been consumed and the buffer flushed, emit exactly one summary object:

```json
{
  "type": "summary",
  "processed_events": 120,
  "duplicate_retries": 3,
  "late_events": 4,
  "alerts_emitted": 2
}
```

`processed_events` counts unique on-time events that were finalized, including approvals. It does not include duplicate retries or too-late events.

Additional required behavior:

1. An identical retry of the current highest `source_seq` for a partition is ignored and increments `duplicate_retries` exactly once.
2. Reusing a partition sequence with different event contents is invalid input and must fail with a useful error.
3. A `source_seq` lower than the highest sequence already observed for that partition is invalid input.
4. Unknown merchants are invalid input.
5. `event_id` must agree across retries of the same partition sequence; a retry with a different ID is conflicting contents.
6. Timestamps must include timezone information. Normalize accepted times to UTC before comparison.
7. `card_fingerprint` and `source_partition` must be non-empty strings; `source_seq` must be a non-negative integer.
8. Same-time finalized events are ordered by `event_id`, not by arrival order or partition.
9. A decline exactly at `t - window_seconds` remains in the active window; only older declines expire.
10. A new alert is allowed exactly at the cooldown boundary.
11. A too-late event does not enter the reorder buffer, does not change merchant counts, and does not trigger an alert.
12. A retry does not advance sequence state beyond the already-recorded event and does not enter the reorder buffer twice.
13. Output must be deterministic across repeated runs over the same logical inputs.

## Production shape

The fixture is small. Design the core for approximately:

- 50,000,000 authorization events per day per process;
- 40,000 active merchants;
- 96 collector partitions;
- 90 seconds of allowed lateness;
- merchant windows between 60 seconds and 20 minutes;
- highly skewed traffic: a few merchants may exceed 20,000 events/second during incidents;
- 512 MB memory budget for detector state;
- sustained throughput target of at least 25,000 events/second on one process;
- alert emission is rare relative to event volume.

A production-credible solution should not repeatedly sort the entire input seen so far, rescan all historical events for every decline, or retain completed windows forever. Be prepared to explain how memory scales with the reorder horizon, active merchant windows, and traffic skew.

You may choose deterministic, heuristic, LLM-assisted, or hybrid techniques, but the observable ordering, boundary, and counting behavior above is exact. Explain why any probabilistic or model-driven component is safe if you use one.

## Expected deliverable

Implement the detector and CLI in `risk_pulse.py`. You may add focused tests or small helper modules.

Your walkthrough should explain:

- how arrival order is reconciled with event-time order;
- what state is retained globally and per merchant;
- how old decline records leave the active window without rescanning history;
- how retries and partition sequence corruption are distinguished;
- expected processing and memory complexity;
- which boundary cases you verified;
- what becomes pathological under a very hot merchant or a large lateness budget;
- whether an LLM or heuristic component belongs in this path, and why.

## In scope

- Python standard library.
- In-memory processing/indexing.
- Focused tests and additional small fixtures.
- Streaming output to stdout.

## Out of scope

- Databases or external caches.
- Distributed watermark coordination.
- Cross-process exactly-once delivery.
- Changing merchant policies while the file is being processed.
- A web UI.

## Run / verify

Baseline checks:

```bash
python3 -m unittest -v
python3 risk_pulse.py --help
```

After implementation:

```bash
python3 risk_pulse.py \
  --merchants fixtures/merchants.csv \
  --events fixtures/events.jsonl
```

Write alerts followed by one summary object to stdout. Diagnostic logging, if any, should go to stderr.

## 60-minute interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other AI tools as you would on the job.

Start by inspecting the fixture ordering and writing down the time and boundary semantics you believe must stay invariant. Implement incrementally and test adversarial ordering, not just the happy path.

The interviewer is evaluating problem decomposition, correctness under event-time constraints, scaling judgment, verification strategy, and your ability to explain and defend the code. Prioritize the processing core over CLI polish.
