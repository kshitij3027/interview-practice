# RackFit — Live Storage Reservation

**HARD · 60-minute AI-assisted customer interview · Python 3.11+**

## Customer message

> We provision scratch space for enterprise batch jobs. Each reservation needs one contiguous span of blocks on a single storage volume, aligned to the job's I/O requirements. Our current service scans every block and sometimes allocates space already reserved by another job. We need a reliable replay of the reservation queue, including releases, retries and failed requests. Volumes are huge, but only a small fraction of their blocks are occupied.

Build one reservation engine. Choose and defend your technical approach; deterministic, heuristic, LLM-assisted or hybrid methods are acceptable if they meet the observable contract. Use AI as you would on the job. Inspect the supplied data, implement incrementally, test your outputs, and explain your tradeoffs within 60 minutes. No credentials, network or external service required.

## Data and starter

- `fixtures/volumes.csv`: `volume_id,pool,capacity` (capacity in blocks). Block addresses start at zero. Each volume belongs to one pool.
- `fixtures/reserved.csv`: `volume_id,start,end` describes permanent occupied spans, half-open `[start,end)`. Rows may overlap, touch, repeat or arrive unsorted; their union is occupied. They cannot be released.
- `fixtures/events.jsonl`: ordered allocation/release requests, including malformed lines. Read one physical line at a time.
- `rackfit.py`: loader, request parser, CLI, and unfinished `ReservationEngine.apply(event)`. Implement that method and any initialization you need. The starter intentionally emits `not_implemented` for valid events.

CSV headers must match the documented columns in any order. IDs are case-sensitive ASCII letters/digits/underscore/hyphen, 1–48 characters. CSV numbers are canonical unsigned decimals, capacity 1..10^12, reserved spans satisfy 0 <= start < end <= capacity. Duplicate identical volume rows are harmless; conflicting definitions, unknown volumes and malformed records fail the whole catalog before output. Every pool in the volume catalog is known.

## Observable contract

Events have a unique operation ID (`event_id`, same ID syntax). Allocation example:

```json
{"event_id":"e1","op":"allocate","pool":"GPU","reservation_id":"job-1","blocks":12,"alignment":8}
```

Release example:

```json
{"event_id":"e2","op":"release","reservation_id":"job-1"}
```

`blocks` must be a JSON integer 1..10^12, and `alignment` one of 1, 8, 64, 512, 4096 (no booleans, floats or strings). The pool must exist. All fields shown are required; extras are ignored. Malformed lines return `{"status":"invalid_event","line":N}` (1-based physical line), with no mutation or operation-ID claim. Valid events are processed in input order. A reservation ID is global across pools and identifies at most one active reservation; it can be reused after release.

For an allocation, first reject an already active reservation ID (`active_id`). Otherwise find the lexicographically smallest volume ID in the requested pool with room for the request; within that volume choose the smallest nonnegative start divisible by alignment such that the entire half-open span fits and intersects neither permanent spans nor active reservations. Return `allocated` with `volume_id,start,end` and mark the span occupied. If none fits, return `no_space` without changing occupancy. Release removes the exact active reservation and returns `released` with its original `volume_id,start,end`; if absent return `not_found`. Free space must become immediately reusable. There is no migration or compaction.

Every valid event result includes `event_id` and `status`, and only `allocated`/`released` add the three location fields. Replaying the same event ID with identical parsed fields returns the original result, even if occupancy has changed or the original attempt failed; it must not change state again. Reusing that ID with different parsed fields returns `event_conflict` and preserves the original record. Invalid events never participate in replay. The engine starts empty of job reservations each CLI run.

Example: on an otherwise free volume with permanent span [0,3), an 8-aligned request for 2 blocks starts at 8, not 3. A request ending exactly at the capacity is allowed. No allocation may straddle volumes, even if total free space is sufficient. Output is one JSON object per input line, in order. No extra stdout diagnostics.

## Production envelope

Up to 10,000 volumes, 256 per pool, 200,000 permanent span rows, 500,000 events and 150,000 simultaneously active reservations. Capacity reaches 10^12 blocks; heavily skewed pools can contain nearly all active reservations. Repeated unsuccessful searches and fragmentation are common. Target: 45 seconds per 500k-event batch after catalog loading, 1 GiB working memory including replay records, on a single ordinary 4-core machine. Explain expected and worst-case work, and measure a representative synthetic workload if time allows. No need to meet a hardware-specific benchmark during the interview, but the design must plausibly scale.

## Run and deliver

From the repository root (no dependencies):

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 rackfit.py --events fixtures/events.jsonl
```

The baseline checks validate the starter plumbing, not the completed capability. Add focused correctness tests. In scope: exact sequential processing, alignment, fragmentation, permanent spans, deterministic choice, releases, idempotency and scalability. Out of scope: HTTP, UI, persistence, concurrent writers, disk I/O and actual storage provisioning. Deliver working code and a concise walkthrough of decisions, complexity and remaining limitations.
