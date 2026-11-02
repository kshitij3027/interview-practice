# CacheFlow — HARD 60-Minute AI-Assisted Customer Interview

## Customer / business context

An edge-content provider caches customer assets in a shared regional node. Every customer has a storage allowance, and the node also has one global storage ceiling. A support team needs to replay a gateway's access and invalidation tape to explain which requests were served from cache, which required origin fetches, and which assets were displaced. The tape arrives out of order, contains delivery retries, and mixes tenant activity. A prototype checks the entire resident catalog after each request and makes incorrect choices when one tenant is busy.

You own the solution strategy and must explain its tradeoffs. Deterministic, heuristic, AI/LLM-assisted, and hybrid approaches are permissible if their observable behavior meets the contract. No external account, package, or API is needed.

## Supplied data

- `fixtures/tenants.csv`: `tenant_id,quota_kb`. The quota is the maximum KB of objects simultaneously resident for that tenant. A zero quota is valid.
- `fixtures/objects.csv`: `object_id,tenant_id,size_kb,ttl_ms`. Objects have one immutable owner, integer size in KB, and fixed lifespan from cache admission. `ttl_ms=0` means the object is never retained.
- `fixtures/events.jsonl`: one event record per **physical** line, including repeated deliveries and intentionally invalid lines. Valid records contain `event_id,at_ms,sequence,kind,tenant_id,object_id`. `kind` is `fetch` or `invalidate`. `at_ms` is event time; `sequence` orders distinct events within one millisecond. The CSV and JSONL files are intentionally not sorted to match one another.

Catalog identifiers are case-sensitive ASCII letters, digits, `_`, or `-`, length 1–48. Event IDs use the same alphabet, length 1–128. CSV integer fields use canonical unsigned decimal digits (no leading zeroes except `0`); `size_kb` is 1..10^9, `quota_kb` is 0..10^9, and `ttl_ms` is 0..10^12. In events, `at_ms` is a JSON integer from 0..10^12 and `sequence` is a JSON integer from 0..10^6. JSON booleans, numeric strings, and floats are not integers. Extra event keys can be ignored; CSV header order can vary.

Identical catalog rows and identical `event_id` replays are harmless. Conflicting catalog IDs, conflicting valid event-ID replays, two **distinct valid** event IDs sharing `(at_ms,sequence)`, malformed catalog rows, or an object owned by an unknown tenant invalidate the **entire input snapshot** before any replay output. By contrast, invalid JSONL lines, invalid event fields, and valid-format events with unknown or cross-tenant object references receive **per-line** errors and do not change state or block later events. A repeated valid `event_id` is applied once, but its original result is printed for every occurrence of that event ID.

## Primary customer request

Implement `CacheReplay.apply(event)` in `cachekit/engine.py`, changing other source files as needed. Replay **distinct valid events in ascending `(at_ms,sequence)` order**, starting with an empty cache. The supplied CLI handles validation, ordering, duplicate delivery, output-line restoration, and invalid-event isolation. The method must calculate the exact result and update its in-memory state.

At the start of **every valid event**, all currently resident objects whose expiration time is `<= at_ms` cease to be resident. Expiration is based on the **most recent cache admission time plus that object's fixed `ttl_ms`**. A cache hit does not extend expiration. Cache expiration and explicit invalidation do not count as capacity evictions.

A `fetch` of a resident, unexpired object is a `hit`: it becomes the most recently accessed resident object. A miss loads the requested object from origin. If its size is greater than the tenant quota or global node capacity, or its TTL is zero, it is `miss_bypassed`: do not retain it and do not displace other entries. Otherwise make room, if necessary, **first inside the requesting tenant** until the tenant can accommodate the object, then **across the entire node** until the global capacity can accommodate it. In each phase, displace the resident object that was least recently successfully fetched (admissions and hits both count as accesses). Resolve an otherwise equal access order by lexicographically smaller `object_id`. An admission is a `miss_cached`. An explicit `invalidate` removes the named object if resident (`removed`) or otherwise reports `absent`; it does not fetch or change access order.

For every successful event, return **exactly** this response shape (example values illustrate formatting, not fixture results):

```json
{"event_id":"example","status":"ok","outcome":"miss_cached","evicted":["A-OLD"],"global_cached_kb":11,"tenant_cached_kb":6}
```

`outcome` is one of `hit`, `miss_cached`, `miss_bypassed`, `removed`, or `absent`. `evicted` contains **only** capacity-driven displacements from this event, sorted by case-sensitive object ID; it is empty for hits, bypasses, and invalidations. `global_cached_kb` and `tenant_cached_kb` are exact integer resident sizes **after** expiration and this event's effects, for the whole node and event's tenant respectively.

## Observable acceptance criteria

- Run `replay` with one compact JSON object per physical input line in original file order, and no diagnostics on stdout. Valid events follow chronological order internally even if their input rows do not. Duplicate event IDs return identical original responses without another state transition.
- Invalid event lines yield `{"event_id":null,"status":"invalid","reason":"invalid_event"}`; preserve a syntactically valid event ID if available. Unknown tenants, unknown objects, and object/tenant mismatches instead use `reason:"unknown_reference"`. These lines have no effect on later results.
- Separate customers may share global capacity but cannot borrow each other's tenant quota. A capacity eviction at the tenant level may change which object would otherwise be removed globally; the required phase ordering is observable.
- A successful hit changes subsequent displacement order without modifying TTL. The exact expiry instant is outside the residency interval. Re-fetching after expiration starts a new lifespan. TTL-zero and oversize objects are never retained.
- Fetching one object twice at distinct times counts as two accesses; identical event-ID replay does not. Invalidation of an absent object is harmless, and a later fetch can re-admit an invalidated object.
- Expired entries never consume quota or appear among `evicted`. When an event arrives after a long idle gap, its output sizes reflect all prior expirations. Zero capacity and quota are supported.
- Results are independent of input row order (except the **required physical output order**), CSV row order, and delivery retries. Different valid events at one millisecond follow their `sequence`, not their file position.
- Malformed snapshot-level catalog conflicts fail with nonzero exit and a stderr diagnostic **before any output**; malformed individual event lines never suppress subsequent valid results.

## Scale and constraints

The fixture is deliberately compact. A production node may contain **300,000 object definitions**, **10,000 tenants**, and **2 million valid events**. The resident set can approach 200,000 objects, with traffic highly skewed toward a few tenants. Limit peak replay working memory to approximately **768 MB** and target average event-processing work substantially below a scan of all resident entries, especially for repeated hits and expiration bursts. The tape may be processed in one offline batch; output order must still match the supplied input. Explain time and memory complexity, worst-case behavior, and any strategy to prevent auxiliary metadata from growing without bound over many accesses.

## Deliverable / scope

Implement the cache replay capability, add adversarial tests, and explain correctness and performance. Keep existing parsing, validation, duplicate handling, and CLI behavior intact. In scope: exact state evolution, quota and expiration semantics, deterministic results, validation and verification. Out of scope: network requests, real wall-clock sleeps, persistence, distributed replicas, compression, object updates, authentication, and UI.

## Setup / verification

Python **3.11+**, standard library only. From this branch's root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 cacheflow.py validate --tenants fixtures/tenants.csv --objects fixtures/objects.csv --events fixtures/events.jsonl --capacity-kb 12
```

After implementing `CacheReplay.apply`, exercise the end-to-end contract with:

```bash
python3 cacheflow.py replay --tenants fixtures/tenants.csv --objects fixtures/objects.csv --events fixtures/events.jsonl --capacity-kb 12
```

The starter already validates input, preserves event ordering and per-line errors, and has a green test baseline. The requested cache-replay behavior is **not implemented**. Existing tests establish the starter contract; they do not cover all feature requirements.

## 60-minute AI-assisted interview instruction

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI assistance as you would during a difficult customer escalation. Inspect the code and representative events, decide what to prioritize, implement incrementally, verify concrete outputs with your own tests, and defend why your result satisfies correctness, throughput, edge-case handling, and memory requirements. Be prepared to describe what you accepted or rejected from generated code.
