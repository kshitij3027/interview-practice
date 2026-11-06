# PulseRank interviewer notes — POST-PRACTICE ONLY

**Never share these notes with the candidate before the practice.** The candidate should recognize the underlying structure, not receive a prescription. These notes apply only to `problem/2026-11-06-pulserank-tail-latency`.

## Underlying structure

The logical catalog is an immutable **two-dimensional time/rank query problem** after revision reconciliation: find rows in a service/region's time interval, calculate exact order statistics over their latency values, count values exceeding a fixed threshold, and find the maximum row with a deterministic secondary/tertiary key. Grouping and sorting by time once is necessary but not sufficient for efficient repeated arbitrary percentiles. This is different from a streaming rate monitor or time-interval peak accumulator; it is range selection on point observations.

## Strong solution options

A high-performing online snapshot design groups latest live rows by `(service_id, region)` and sorts each group by `(at_ms, request_id)`; binary search identifies the `[lo,hi)` range for a query. Compress latency coordinates per group. A **persistent frequency segment tree** (or an equivalent wavelet-tree/matrix index) built over successive time-sorted prefixes can answer count/order-statistic comparisons between two versions. For nearest-rank p, compute `k=(p*n+99)//100` and descend the difference of version counts to find the k-th smallest latency. Count values `> budget_us` with a threshold count query or equivalent rank prefix. A standard static range-maximum segment tree (or sparse table with safe tie-breaking) on `(-latency_us, at_ms, request_id)` identifies the deterministic slowest within the time span. For completely empty groups, return null percentiles and slowest, not a default fabricated measurement.

Let `N` be total latest live rows, `D` distinct latency values within a group, `Q` queries. Sort/preprocess roughly `O(N log N + N log D)` and answer each query in `O(log N + log D)` for rank, breach, and range-max work (two rank queries add only a constant factor). Persistence uses `O(N log D)` node storage. Python boxed node tuples for millions of rows can breach 1 GB; packed integer arrays, succinct wavelet representations, or suitable chunking are important. A merge-sort tree can answer threshold counts in `O(log^2 N)` and find percentiles with an additional binary search over values, slower but defensible if benchmarks fit. An offline rearrangement such as Mo's algorithm plus a mutable frequency structure is defensible for bounded query batches; justify memory and run time on skew. A correct `O(m log m)` per-query scan for local fixture data is useful as an oracle but cannot be the final full-credit approach.

## Why naive approaches fail

- Looping through all 2 million revisions for every investigation multiplies work by 250,000 and risks counting old revisions.
- Sorting the selected latencies on every query repeats expensive work on heavily overlapping windows.
- Treating percentile as interpolated or average median gives incorrect exact outputs for small or tied samples.
- Grouping by original service/region before choosing latest revision leaves moved requests in multiple groups.
- Picking any one of equal slowest durations leaks CSV order into output; using lexicographic IDs before timestamps also fails.
- Counting at inclusive end-of-window or using floating time arithmetic creates boundary defects.
- Memory blowups from Python objects or unbounded duplicates invalidate the scale rationale.

## Fixture discoveries and hidden checks

The fixture has 8 unique scopes (one duplicate scope row), 25 physical observations including one identical replay of `req-g2` revision 3, 18 logical request IDs, 16 final live requests and two latest cancellations (`req-g4`, `req-z1`). `req-g1` moves from US to EU on revision 2, while `req-g2`'s revision 3 precedes revision 2 in the file. `req-auth1` moved from time 0 to time 1. `req-g8` and `req-g9` tie in both latency and timestamp; `req-g6` has the same maximum latency earlier in time. These are not incidental!

Expected key fixture results (all requests are independent):

| Query | Count | p50_us | p95_us | over_budget | slowest_request_id |
|---|---:|---:|---:|---:|---|
| `g-wide` in `us-west` `[100,121)` | 7 | 180000 | 400000 | 4 | `req-g6` |
| `g-early` `[100,103)` | 1 | 180000 | 180000 | 1 | `req-g3` |
| `g-tail` `[120,121)` | 3 | 400000 | 400000 | 2 | `req-g8` |
| `g-idle` `[200,400)` | 0 | null | null | 0 | null |
| `g-wide` in `eu-central` `[100,121)` | 1 | 90000 | 90000 | 0 | `req-g1` |
| `billing` `us-west` `[100,112)` | 2 | 200000 | 350000 | 1 | `req-b2` |
| `auth` `[0,1)` | 0 | null | null | 0 | null |
| `whole` `video` `[0,10^12)` | 1 | 1000000000 | 1000000000 | 1 | `req-v1` |

More checks to generate after interview: conflicting replay of a superseded `(request_id,revision)` is still a snapshot failure; conflicting duplicate scope; invalid cancelled row with leftover timestamp; numeric strings or booleans in queries; timestamp at exactly `until_ms`; scope with no live rows; 1000 identical latency values; 1000 tied timestamps with lexicographic winner; large latency limits and 32-bit boundaries; randomized shuffled records; changed request ID latest revision moving scopes; repeated query IDs; 100,000 query windows concentrated on one group; multiple revisions of one ID out of order; invalid JSONL line between valid queries. Test correctness with a tiny brute-force oracle but run a distinct scale test to assess complexity.

## Recommended 60-minute prioritization

Minutes 0–10: inspect fixtures, source contracts, and error handling; articulate exact population/rank and scaling. Minutes 10–25: build correct per-scope latest-live dataset and implement a basic oracle to understand expected results. Minutes 25–45: add a reusable query index for percentiles and counts; keep slowest tie order deterministic. Minutes 45–55: adversarial tests, CLI verification, compare against oracle. Final 5: walk through amortized costs, memory, and deployment limits. If pressed for time, prioritize exact correctness and a defensible scalable design rather than unverified agent-generated complexity.

## Alternative defensible designs and likely AI-agent failure modes

Accept specialized sorted vectors or succinct rank structures, static merge-sort structures, offline frequency-query approaches, and hybrid techniques when their outputs are exact and the candidate has realistic complexity/memory evidence. A pure LLM choice is unlikely to meet exact reproducibility and volume targets, but AI is welcome as implementation assistance. Watch for agents that one-shot a pandas groupby, calculate p95 with NumPy interpolation, use Python `statistics.median` (even-size average), drop revisions by CSV last occurrence, use `<=until_ms`, ignore the moved request, inadvertently expose evaluator tests, or claim `O(log N)` with an actual per-query re-sort. Verify what the candidate can explain unaided.

## Interviewer walkthrough inspection points

Ask the candidate to trace `req-g2` (revisions 1,3,2,3), `req-g1` moved scope, and `req-g4` cancellation. Check both percentile ranks on an even-size window, strictly greater breach threshold, tie winner order, nearest-rank when n=1, query error isolation, and output order. Inspect memory layout and repeated-query benchmark rather than relying only on local fixture counts. Confirm no candidate-facing source or history contains this document or the grading rubric.
