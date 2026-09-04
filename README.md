# CargoSlot — One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A cargo terminal operates multiple screening lanes at each airport site. Every outbound shipment has a pre-booked 15-minute screening slot, but lanes sometimes become unavailable because of equipment faults, safety inspections, or staffing incidents.

Today, dispatchers recover from an outage manually. They move the shipments that were booked into the unavailable lane/time range while leaving all unaffected bookings fixed. This becomes difficult when shipments have different handling requirements, narrow arrival windows, and different business priorities.

The terminal wants a deterministic recovery planner that can answer many independent outage scenarios against the same baseline day schedule.

## Supplied data

### `fixtures/lanes.csv`

Each lane has:

- `lane_id` — globally unique lane identifier.
- `site` — airport/site code.
- `capabilities` — `|`-separated capability tokens supported by the lane.
- `open_from` — first usable slot start, UTC.
- `open_until` — exclusive end of the lane's operating window, UTC.

Every usable slot is exactly **15 minutes** and all fixture timestamps are aligned to 15-minute boundaries.

### `fixtures/bookings.csv`

Each baseline booking has:

- `shipment_id` — unique shipment identifier.
- `site` — site at which the shipment must be screened.
- `lane_id` — currently booked lane.
- `slot_start` — current 15-minute slot start.
- `required_capability` — capability the replacement lane must support.
- `earliest_start` — earliest allowed replacement slot start, inclusive.
- `latest_start` — latest allowed replacement slot start, inclusive.
- `priority` — positive integer business priority.

A shipment occupies exactly one lane for one 15-minute slot.

### `fixtures/outages.jsonl`

Each line is an independent planning request containing:

- `outage_id`
- `site`
- `lane_ids` — one or more lanes unavailable for the outage.
- `start` — inclusive outage start.
- `end` — exclusive outage end.

Outage boundaries are aligned to 15-minute slots. Outage requests are **independent**: do not carry rebookings from one outage into the next request.

## Goal

Complete the recovery planner so every outage request produces the best feasible reassignment plan for the baseline schedule.

Only bookings whose current `(lane_id, slot_start)` falls inside that outage need to be reconsidered. All other baseline bookings stay fixed and continue to occupy their original lane/slot.

An impacted shipment may move to any lane at the same site when all of the following are true:

1. the lane supports the shipment's `required_capability`;
2. the candidate slot is within the lane's operating window;
3. the candidate slot is within the shipment's inclusive `[earliest_start, latest_start]` window;
4. that lane/slot is not unavailable under the outage;
5. that lane/slot is not occupied by an unaffected baseline booking;
6. no other impacted shipment in the same recovery plan is assigned there.

A shipment may remain unassigned when no globally feasible plan can place it.

## Plan quality

Among all feasible plans for the impacted shipments, choose a plan using these objectives **in order**:

1. **Maximize the sum of `priority` for assigned impacted shipments.**
2. Subject to (1), **maximize the number of assigned impacted shipments.**
3. Subject to (1) and (2), **minimize total displacement minutes**, where a shipment's displacement is `abs(new_slot_start - original_slot_start)` in minutes. Changing lanes at the same time adds no extra displacement beyond the time difference.

If several plans are still tied, any one is acceptable, but your implementation must choose consistently across repeated runs and must not depend on CSV/dictionary iteration order. Be prepared to explain your deterministic tie rule.

## Observable requirements

For each outage, write exactly one JSON object to stdout:

```json
{
  "outage_id": "out-001",
  "assignments": [
    {
      "shipment_id": "S-101",
      "lane_id": "JFK-04",
      "slot_start": "2026-09-04T09:15:00Z"
    }
  ],
  "unassigned": ["S-109"],
  "assigned_priority": 27,
  "assigned_count": 3,
  "total_displacement_minutes": 30
}
```

Additional required behavior:

1. `assignments` must be sorted by `shipment_id`; `unassigned` must be lexicographically sorted.
2. Output timestamps must be normalized to UTC with a `Z` suffix.
3. A lane slot is unavailable exactly when its slot start satisfies `outage.start <= slot_start < outage.end` and its lane is listed in the outage.
4. A candidate at exactly `earliest_start` or `latest_start` is valid.
5. A slot starting at `open_until` is invalid because the 15-minute booking would begin outside the operating window.
6. An impacted shipment's original booking is removed from fixed occupancy before planning. Impacted shipments must not block one another at their old locations.
7. Unaffected bookings never move, even if moving one could create a better overall recovery plan.
8. Capability matching is exact token membership. `cold` does not match `cold-chain` unless both tokens are explicitly present.
9. A shipment cannot change sites.
10. Reordering rows in `lanes.csv` or `bookings.csv` must not change the plan quality or cause nondeterministic output.
11. Duplicate `shipment_id` or `lane_id` values are invalid input.
12. A booking that references an unknown lane, a lane at a different site, an unsupported capability, or a slot outside that lane's operating window is invalid baseline data and must fail fast.
13. Baseline bookings may not double-book a lane/slot. Treat that as invalid input.
14. Every shipment window must be aligned to 15-minute boundaries and satisfy `earliest_start <= slot_start <= latest_start`.
15. Outages must reference known lanes at the declared site, have aligned boundaries, and satisfy `start < end`.
16. An outage may include a lane that has no impacted bookings; this is valid.
17. If there are no impacted bookings, return an empty successful plan with all numeric totals equal to zero.
18. Planning requests are read-only. Processing one outage must not mutate the baseline schedule seen by later outage requests.

## Production constraints

The checked-in fixture is intentionally small. Design and explain your approach for approximately:

- 35 terminal sites;
- 4,000 lanes total;
- 900,000 baseline bookings per day;
- 2,000 independent outage-planning requests per day;
- typical outage: 20–400 impacted shipments;
- severe outage: up to 8,000 impacted shipments;
- shipment replacement windows usually span 1–12 slots, but may span up to 96 slots;
- 2–6 compatible lanes per shipment in the common case, with a few broad `general` capabilities matching hundreds of lanes;
- target p95 under **750 ms** for typical outages after baseline preprocessing;
- memory budget of **1 GB** for the process.

A production-credible solution should preprocess the static baseline once, avoid rescanning all 900k bookings for every outage, avoid enumerating slots that can never satisfy a shipment, and avoid brute-forcing every combination of assignments.

The exact business objectives above matter: a greedy "highest priority first, first free slot" implementation can produce a lower-priority total or unnecessary displacement when shipments compete for scarce compatible slots.

## Expected deliverable

Implement the planner behind `cargo_recovery.py`. You may add focused tests or small helper modules.

Your walkthrough should explain:

- how you identify impacted versus fixed bookings efficiently;
- how you represent candidate lane/slot choices;
- how your approach guarantees the three optimization objectives in order, or where it deliberately trades exactness for scale;
- expected preprocessing, per-outage time, and memory complexity;
- how high-contention slots or broad capabilities affect performance;
- which adversarial fixture cases you verified;
- why your tie handling is deterministic;
- whether a heuristic, LLM-based, or hybrid component belongs in the critical planning path, and why.

## Verification / run commands

Baseline checks before you change anything:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q cargo_recovery.py recovery tests
python3 cargo_recovery.py --help
python3 cargo_recovery.py validate \
  --lanes fixtures/lanes.csv \
  --bookings fixtures/bookings.csv \
  --outages fixtures/outages.jsonl
```

After implementing the planner:

```bash
python3 cargo_recovery.py plan \
  --lanes fixtures/lanes.csv \
  --bookings fixtures/bookings.csv \
  --outages fixtures/outages.jsonl
```

Write one JSON object per outage to stdout. Diagnostic logging, if any, should go to stderr.

## In scope

- Python 3 standard library.
- In-memory preprocessing/indexing.
- Focused tests and additional compact fixture cases.
- Exact, heuristic, LLM-assisted, or hybrid techniques if you can defend them against the stated correctness and scale requirements.

## Out of scope

- Databases, Redis, or external schedulers.
- Distributed coordination.
- Multi-slot shipments or variable screening durations.
- Moving unaffected bookings.
- Persisting recovery plans.
- Authentication or a web UI.

## 60-minute AI-assisted interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other AI tools exactly as you would on the job.

Start by inspecting the supplied schedule and outage fixtures. Write down the invariants and plan-quality objectives before selecting an approach. Implement incrementally, verify contention cases rather than only obvious moves, and leave enough time to explain complexity and tradeoffs.

The interviewer is evaluating how you turn a customer scheduling problem into a correct technical model, how you reason about global rather than local choices, how you use AI without blindly trusting it, how you verify the result, and whether you can defend the solution under production constraints.
