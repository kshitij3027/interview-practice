# POST-PRACTICE ONLY — INTERVIEWER NOTES

Do not show this file to the candidate before or during the exercise.

## Intended underlying problem structure

The strongest exact batch solution treats each region independently and processes its valid queries in chronological order, even though final answers must be restored to original query-file order.

For one region with window length `W`:

1. Sort that region's deduplicated events by `(occurred_at, event_id)`.
2. Sort valid queries by `(as_of, original_query_index)`.
3. Sweep forward through query time while maintaining a rolling event window satisfying `(as_of - W, as_of]`.
4. Add all events with `occurred_at <= as_of`.
5. Evict all active events with `occurred_at <= as_of - W`.
6. Maintain, for each client:
   - active request count;
   - a credential -> active occurrence count map;
   - distinct credential count.
7. Maintain a dynamic ranking structure keyed by `(-distinct_credentials, -request_count, client_id)` so extracting the top `k` does not require sorting every active client from scratch.

In Python's standard library, a practical interview implementation is a versioned heap with lazy invalidation plus periodic compaction. Each client score change increments a version and pushes a new heap entry. On extraction, stale versions are discarded. Pop the current top `k`, record them, then push those same current entries back. If the heap becomes much larger than the number of active clients, rebuild it from current client state so stale entries cannot grow without bound.

A balanced ordered set would also be natural in a language/library that provides one. The exact implementation is less important than preserving exact ranking while reusing rolling-window work.

## Strong solution complexity

Let `E_r`, `Q_r`, and `C_r` be event, query, and active-client counts for one region.

Typical batch costs:

- sort: `O(E_r log E_r + Q_r log Q_r)`;
- each event enters once and leaves once;
- per enter/leave state update: expected `O(1)` for credential refcounts plus `O(log C_r)` if the ranking structure is updated;
- each query: roughly `O(k log C_r)` plus amortized stale-entry cleanup;
- memory: active-window occurrence state plus per-client credential refcounts, ranking state, and loaded/sorted batch representation.

At the production scale in the README, a candidate should notice that Python object overhead for tens of millions of events can dominate the 1.5 GB budget. Good discussion includes compact representations, region-at-a-time processing, external sorting/streaming from validated files, or a more memory-efficient runtime. The interview implementation can still load the fixture in memory.

## Why naive approaches fail

### Per-query corpus scan

Correct on tiny fixtures but approximately `O(E * Q)` and completely non-credible for tens of millions of events plus hundreds of thousands of queries.

### Rebuild a set of credentials for each query

Still repeats nearly all work across nearby historical queries.

### Plain set for active credentials

Wrong when the same credential occurs more than once in the window. If the oldest occurrence expires, deleting the credential from a set loses the newer still-active occurrence. A refcount/multiset is required.

### Sort all active clients for every query

Produces correct fixture answers but costs roughly `O(Q * C log C)` in hot regions. The problem explicitly asks for a more incremental top-k strategy.

### Process queries only in input order

Because query times move backward and forward, a forward-only window cannot be reused directly in input order. The clean batch approach sorts internally and restores original output ordering.

### Compare RFC3339 strings

Offset-equivalent timestamps may have different textual forms. Normalize to instants.

## Subtle traps

1. Window is `(as_of - W, as_of]`, not `[start, end)`, not `[start, end]`.
2. Events at exactly `as_of` count.
3. Events at exactly `as_of - W` do not count.
4. Deduplicate exact `event_id` retries before ranking semantics.
5. `request_count` counts repeated credential events individually after retry deduplication.
6. `distinct_credentials` counts a credential once while one or more occurrences remain active.
7. When an occurrence expires, decrement the credential refcount; only remove the distinct credential when the refcount reaches zero.
8. Ranking tie-break is lexicographically smaller client ID.
9. Unknown region and invalid `k` are query-level failures, not dataset failures.
10. Internal query sorting must not change output order.
11. A shared credential ID across two clients is two independent per-client distinct memberships.
12. Heap lazy-deletion implementations can return stale scores unless version validity is checked on every pop.

## What should be discovered from the supplied data

- `e-us-5` appears twice identically and must count once.
- Client `c-a` uses `us-card-1` at both `09:51` and `09:58`; at `10:01`, the older occurrence is out of the 10-minute window while the newer one remains.
- `q-us-later` appears before `q-us-base`, so file order is not chronological.
- `c-c` has an event at exactly `09:50` for the `10:00` US query; it is excluded by the left-open boundary.
- `c-c` also has an event at exactly `10:00`; it is included by the right-closed boundary.
- `q-eu-offset` uses `12:05+02:00`, which is the same instant as `10:05Z`.
- `c-b` and `c-d` tie on the base US query after the first two ranking dimensions; `c-b` wins the lexical tie-break.
- APAC has repeated `ap-card-1` plus a second credential, which exposes the difference between request count and distinct count.

## Expected fixture outputs

In the original query-file order:

1. `q-us-later`: `c-b (2,3)`, `c-a (2,2)`, `c-d (2,2)`.
2. `q-eu-offset`: `c-e (1,2)`, `c-f (1,1)`.
3. `q-us-base`: `c-a (2,3)`, `c-b (2,2)`, `c-d (2,2)`.
4. `q-us-empty`: empty leaders.
5. `q-apac`: `c-h (2,3)`.
6. `q-unknown-region`: invalid / `unknown_region`.
7. `q-too-many`: invalid / `invalid_k`.
8. `q-zero-k`: invalid / `invalid_k`.

Tuple notation above is `(distinct_credentials, request_count)`.

## Hidden checks to use during evaluation

- Same client/credential at `09:51` and `09:58`; query at `10:01` must keep the credential after the first occurrence expires.
- One event exactly at the left boundary and one microsecond after it.
- One event exactly at query time.
- Several clients tied on both numeric ranking dimensions; lexical client ID must decide.
- Query order intentionally `later, earlier, later`.
- Same credential ID used by two clients.
- Event rows fully shuffled.
- Exact duplicate `event_id` versus same ID with changed credential.
- Query with valid region but `k = max_k + 1` followed by a valid query.
- Offset-equivalent timestamps such as `10:00Z` and `12:00+02:00`.

## Alternative defensible designs

- A language-provided ordered multiset/tree keyed by current client score can replace the heap and avoids stale-entry management.
- For very small `max_k`, bucketed score indexes can be defensible if score ranges are bounded or compressed, but the candidate must explain bounds and update costs.
- If queries are sparse, a different batch strategy may trade memory for recomputation. The candidate should quantify it rather than claim it is universally better.
- Approximate heavy-hitter sketches are not contract-preserving here because exact ranking and tie-breaking are required; they are only acceptable if explicitly presented as a deliberate production tradeoff outside the exact contract.
- An LLM has little value in the critical ranking loop. AI is useful for implementation, test generation, and reasoning, not for replacing deterministic event-time semantics.

## Likely AI-agent failure modes

- Writes a one-shot per-query scan because the fixture is small.
- Uses a set of credentials and removes too early during eviction.
- Gets the boundary as `[start, end)` out of habit.
- Sorts query results chronologically and forgets to restore input order.
- Uses timestamp strings directly.
- Rebuilds/sorts the whole leaderboard on every query.
- Uses a lazy heap but never validates stale entries.
- Uses lazy heap versions but lets stale entries grow without any memory-control story.
- Treats duplicate credential observations as duplicate delivery events.
- Rejects unknown query regions during dataset load instead of emitting a query-level invalid result.

## Recommended 60-minute prioritization

- 0–10 min: read fixture/semantics, write down window boundaries and ranking key.
- 10–20 min: choose batch ordering and rolling state representation.
- 20–40 min: implement event insertion/eviction and query answering.
- 40–50 min: add top-k structure and restore original output order.
- 50–57 min: test duplicate credential eviction, boundaries, and ties.
- 57–60 min: prepare complexity/memory explanation and identify production compromises.

## Walkthrough inspection points

Ask the candidate to show:

1. exactly where the left-open boundary is enforced;
2. the state used for repeated credentials;
3. how one client ranking update invalidates/replaces prior ranking state;
4. how stale ranking entries are recognized;
5. how internal chronological processing maps back to query-file order;
6. complexity for one event enter/leave and one top-k query;
7. memory behavior for a client with millions of events but few distinct credentials;
8. what they would change first if the full production batch could not fit in memory.
