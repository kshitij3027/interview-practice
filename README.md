# CostCanopy — HARD 60-minute AI-assisted customer interview

## Customer / business context
A cloud-finance team allocates infrastructure charges across a hierarchy of cost centers. An engineer can belong to a small team inside a department inside a business unit. Finance can post a charge, correct its amount or reporting center, or void it entirely. Ingest retries can replay previously accepted changes. Today, the reporting dashboard re-sums every descendant charge whenever an executive opens a cost-center rollup; on large organizations it freezes, and corrections sometimes double bill a department.

You own the technical approach. Choose deterministic, heuristic, AI-based, or hybrid techniques as you see fit, but the behavior below must be exact, explainable, and efficient.

## Supplied data
- `fixtures/centers.csv`: `center_id,parent_id,budget_cents`. A blank parent is a root; there may be multiple roots. Each cost center has at most one parent. IDs are case-sensitive ASCII letters/digits/`_`/`-`, length 1–32. Budgets are canonical base-10 integers in `[0,10^12]`. A center's budget is **its own threshold for its entire reporting group**; do not add children's budgets. Identical replays of catalog rows are harmless; conflicting reuse, missing parents, and cycles make the entire catalog invalid.
- `fixtures/operations.jsonl`: one JSON object per physical line, in arrival order; some lines are intentionally invalid. Every valid record has a nonempty string `request_id` of at most 128 characters (the value need not be unique) and a `type`. Mutations additionally have an `event_id` (same ID format as centers) and `charge_id` (same ID format). Query records have no event ID. Extra fields may be ignored.

## Primary customer request
Implement a stateful charge-allocation processor that reads one catalog and the operations stream, applies changes **in stream order**, and returns one JSON response per physical input line. The service is queried while ingest is happening; prior outputs cannot be revised.

There are four record types:

1. `post`: `request_id,type,event_id,charge_id,center_id,amount_cents`. Create a **never-before-seen** charge, assigned to the specified center. `amount_cents` must be an integer in `[0,10^12]` (booleans are not integers). Zero-value charges are active and count toward `active_charges`.
2. `revise`: same fields as `post`. Atomically replace the amount **and** assigned center for an existing active charge; either or both may stay unchanged.
3. `void`: `request_id,type,event_id,charge_id`. Deactivate an existing active charge. A voided charge ID may not be posted again.
4. `summary`: `request_id,type,center_id`. Return the current total **amount and number of active charges assigned anywhere in that center's descendant group, including itself**. The response also reports that center's own budget and whether the total is strictly greater than the budget.

Successful mutations return exactly `{"request_id":"...","status":"applied","event_id":"..."}`. A replay of an **already successfully applied** `event_id` with the same type and business payload returns exactly the same shape with `"status":"duplicate"`, with no state change, **even if the original charge was subsequently revised or voided**. `request_id` is not part of business-payload equality; replay delivery can have a different request ID. Reusing an applied event ID with a different payload is invalid (`event_conflict`) and changes nothing. Failed mutations never reserve an event ID. A different event ID applied to the same charge is a new request, not an automatic replay.

Successful summaries return exactly:

```json
{"request_id":"q","status":"ok","center_id":"ENG","total_cents":1234,"active_charges":2,"budget_cents":100000,"over_budget":false}
```

This illustrates the response shape, not an answer to the supplied fixture. Monetary totals are exact integers in cents; no rounding, floating-point arithmetic, or negative charge balances.

## Observable acceptance criteria
- Every input line produces exactly one compact JSON object on stdout in the same order. Diagnostic messages belong on stderr. An invalid line does not prevent processing later lines.
- For malformed JSON, non-object values, unknown `type`, missing/invalid fields or IDs, invalid `amount_cents`, return `{"request_id":null,"status":"invalid","reason":"invalid_record"}`; preserve the parsed `request_id` if it is a valid nonempty string of length at most 128.
- For syntactically valid records: unknown `center_id` returns `unknown_center`; posting a previously used `charge_id` returns `charge_exists`; revising or voiding a never-seen charge returns `unknown_charge`; revising or voiding a previously voided charge returns `inactive_charge`; conflicting reuse of an applied `event_id` returns `event_conflict`. All use `status:"invalid"` and `reason` with the names given, plus `request_id`.
- Validate the record's fields before comparing replay IDs. Exact applied-event replays take precedence over the charge's current state. Invalid events never reserve their ID. For summary requests, apply the current snapshot only; do not retroactively modify prior responses.
- Descendant membership includes the center itself, excludes ancestors/siblings and unrelated roots, and is not affected by row order. A revision between centers updates both groups exactly once. A void reverses the current value and active-count contribution exactly once. An unchanged revision is still a successful mutation with a new event ID.
- At budget equality `over_budget` is false; at budget zero one cent is over. Repeated `request_id` values are independent requests. Event IDs and charge IDs are case-sensitive.

## Production constraints
One long-running snapshot can have up to **250,000 cost centers**, **2 million successful charge IDs**, and **3 million mixed operation/query lines**. A reporting hierarchy might be a chain 250,000 levels deep. Expect skewed centers, frequent revisions across distant branches, bursts of repeated summaries, repeated delivery events, and out-of-order business corrections (process those strictly by their stream position). Target **768 MB working memory** and **15 ms typical p95 per event or summary** after loading on a modern machine. These are targets to benchmark and defend. Updating every ancestor or scanning all descendant charges on every query does not satisfy the production requirement. Avoid assumptions that recursion depth is small.

## Scope / expected deliverable
Implement the processor and any supporting modules or tests. The supplied catalog loader, syntax checker, CLI, and starter tests already work; `process` deliberately emits `not_implemented`. In scope: correct state transitions, exact cost-center summaries, replay safety, per-line validation, efficient scale, and complexity/tradeoff explanation. Out of scope: persistence across runs, auth, real billing integration, exchange rates, changing the reporting hierarchy, historical as-of queries, changing budgets, or a frontend. Do not rewrite fixture data to make tests pass.

## Setup and verification
Python 3.11+, standard library only. From the repository root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 costcanopy.py check --centers fixtures/centers.csv --operations fixtures/operations.jsonl
```

After implementing the processor:

```bash
python3 costcanopy.py process --centers fixtures/centers.csv --operations fixtures/operations.jsonl
```

The green starter tests cover catalog loading, input syntax inspection, and the command harness, **not** the requested charge-allocation feature.

## 60-minute AI-assisted interview instruction
You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools as you would on a customer escalation. Inspect the data, decide how to represent active charges and reporting groups, implement incrementally, add adversarial checks, run the provided commands, and explain correctness, runtime/memory bounds, replay behavior, and your tradeoffs. Your walkthrough matters as much as the code you generate.
