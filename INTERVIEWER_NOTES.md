# POST-PRACTICE ONLY — CacheFlow Interviewer Notes

**Do not show to the candidate before or during the 60-minute exercise.** These notes intentionally disclose the underlying structure, approaches, and hidden checks.

## Underlying structure

This is a deterministic **event-sourced cache simulator** with two independent LRU eviction scopes (per-tenant and global), a **fixed-admission TTL** lifetime, chronological deduplicated replay, and output restoration by original physical line. The provided parser/runner already performs the latter data ingestion responsibilities. The hard part is maintaining a consistent *single resident set* indexed simultaneously by object ID, tenant recency, global recency, expiration and size totals, with no linear scans for typical events.

## Strong approaches

A clean Python solution uses `dict[object_id, Resident(admitted_ms, expires_at, last_access, size, tenant)]`, `OrderedDict` (or linked ordered maps) for a global LRU and one LRU per tenant, and a min-heap of `(expires_at, generation, object_id)` for expiration. On each valid event, expire entries with `expires_at <= at_ms` and verify a heap entry still represents the current admission (generation prevents removal of a re-admitted object). Remove a resident atomically from all three views and both KB counters. On hit, move object to the MRU end in both LRU views; do **not** change `expires_at`. On eligible miss, evict from the requesting tenant until its quota fits, then globally until global capacity fits, then admit as MRU and push expiration. On invalidation, remove if present, but do not list it as an eviction. For oversize/TTL-zero, bypass before capacity eviction. Sort evicted IDs in the reply only.

An alternative uses binary heaps for recency with lazy entry invalidation, or an indexed heap/tree for expiration and ordered indexes. Lazy approaches must explicitly control metadata growth: 2 million hits to a single object must not retain 2 million stale heap records. Periodic heap rebuild when stale entries greatly outnumber current residents, an indexed heap with deletions, or a bounded-generation strategy can work. The expiration heap also needs bounded stale entries after invalidations/re-admissions, not just successful expiry. `OrderedDict` moves are O(1) average; expiration insertion/removal is O(log C); each resident admission expires/evicts at most once, so total expiry processing is amortized. Total is O(E log E + E log C) for parsing/sorting and replay, O(E + O + T + C) memory including input/output, for E events, O object definitions, T tenants and C residents. With compaction, expiry-heap memory is O(C) rather than O(E). A batch sort dominates if event timestamps are unordered.

An exact reference oracle for tiny tapes can use a straightforward resident dict, expire by scanning it before every event, select minimum `(last_access_order, object_id)` among tenant or global residents, and record output. It is intentionally too slow at scale but suitable for differential testing.

## Why naive approaches fail

Scanning all residents to find expirations and eviction victims for each hit costs O(E*C). A single global LRU breaks tenant quotas. A tenant-only LRU ignores global contention. Refreshing TTL on hit changes fixed-admission semantics. Using physical file order produces incorrect results from the shipped fixture. Treating event IDs as action IDs rather than idempotency keys double-counts retries. Applying a capacity eviction before recognizing TTL-zero/oversize bypass needlessly deletes content. Expiring an object without removing it from both recency orders or both counters corrupts subsequent decisions. Keeping a priority heap entry for every hit without stale-entry control can exhaust memory.

## Hidden checks / subtle traps

1. Global capacity 0 and nonzero tenant quota: fetch bypass, no residency; invalidation absent. Tenant quota 0 and nonzero global capacity: bypass.
2. Object size exactly equal to tenant or global capacity is admissible; **greater** is bypassed without eviction.
3. At `at_ms == admitted_ms + ttl_ms`, a previously cached object is expired. A hit at `expiry-1` does not extend this boundary.
4. Later fetch after expiration is a new admission; stale expiry-heap tickets from the former admission must not evict the new resident.
5. Same millisecond with sequence 1 and 2: the sequence-1 fetch affects the sequence-2 result. Physical JSONL order is irrelevant to state.
6. Identical `event_id` replay has one state transition and two identical output objects, even when its repeated physical line appears between other event rows.
7. A busy tenant spills over its local quota before global pressure; a global eviction can target a different tenant. The order of the two phases changes victim lists.
8. Expiration removes entries before **invalidate** as well as before fetch. An expired target invalidates as `absent` and the output counters exclude other expired entries.
9. Oversized/TTL-zero fetch leaves previous objects and their access order unchanged. Invalidate never makes an object MRU.
10. Capacity evictions are reported sorted by ID, **not** by chronological victim selection. TTL expiry and invalidations never appear in `evicted`.
11. Repeated hits on a single resident at large scale must not leave unbounded recency heap records. Lots of early invalidations can likewise make expiration heap stale; inspect memory compaction.
12. Invalid per-line events with unknown/cross-tenant references or boolean integers must not influence ordering/residency. Conflicting *valid* replay IDs and duplicate chronological positions are fatal before output.

## What fixture inspection should reveal

`events.jsonl` is out of chronological order and repeats `E-11`. There are same-millisecond but separately sequenced events, an immediate-expiry object (`A-ZERO`), an object larger than its owner's quota (`B-HEAVY`), explicit invalidations, a later request at an expiry boundary, and individual malformed event lines. Catalog rows include benign duplicate deliveries. Global capacity 12 and tenant quotas 8/6/20 produce both local and global contention.

## Alternative defensible designs

An indexed expiration tree with removable nodes instead of a heap avoids lazy stale tickets. A doubly linked per-tenant/global list with a hashmap gives the same key recency operations as `OrderedDict`. A batched sorted event pass with small object set and a scan-based oracle may be useful for tests but cannot be the production answer. A deterministic model is well suited to the exactness requirement; LLMs might help generate edge-case tests or code but do not justify approximating defined semantics. Discuss persistence and parallelism only as future extensions.

## Likely AI-agent failure modes

Generated code often chooses one LRU order, silently interprets TTL as sliding, neglects per-tenant eviction order, evicts the incoming item during global pressure, loses previous outputs when physical lines are shuffled, increments size counters twice, uses `heapq` with no stale-record policy, or assumes every field named `sequence` is valid because `bool` subclasses `int` in Python. One-shot agent solutions may pass the fixture's baseline tests while leaving exact outputs and concurrency-like replay traps wrong.

## Suggested 60-minute prioritization

First 5–8 minutes: inspect fixtures, parser, and event boundaries; clarify contract. Next 12 minutes: define invariant and resident representation, test one hit/miss/expiry. Next 20–25 minutes: two-scope displacement, invalidation, and exact counters. Next 10 minutes: adversarial tests for TTL boundary, local-before-global eviction, replay and stale metadata. Final 5–10 minutes: run commands, discuss complexity and scaling. Strong partial completion prioritizes correctness of state transitions over UI or unrelated infrastructure.

## Walkthrough inspection points

Ask the candidate to locate the authoritative resident map, trace all removal paths through every index/counter, justify why a hit does not change expiry, demonstrate how a repeated event returns the original output, explain priority when both local and global quota are exceeded, and estimate peak memory after 1 million hits to one item. Require an explicit description of the branch's green starter baseline versus new feature tests, plus an AI-generated-code verification example.
