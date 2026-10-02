# INTERVIEWER NOTES — POST-PRACTICE ONLY

## Intended underlying problem structure

This is an exact repeated spatial radius and top-k search over an immutable set of geographic points with static business filters. The candidate-facing README intentionally does not name a spatial index. Recognizing that reusable geographic search state is needed is part of the interview.

One strong deterministic design maps latitude/longitude to 3D unit-sphere coordinates `(cos(lat)cos(lon), cos(lat)sin(lon), sin(lat))` and builds a balanced spatial search structure. For radius `r`, the unit-sphere chord threshold is `2*sin(r/(2R))`. A region may be pruned only when a proven lower bound exceeds that threshold. Every surviving point still uses the supplied exact `great_circle_meters` helper before it is returned.

Conservative hierarchical geographic tiling or a metric tree can also be defensible. The important properties are exactness, safe pruning across the date line and poles, reusable preprocessing, and localized query work.

## Strong approaches and complexity

Pre-validate the immutable snapshot once. Model parcel size ordinally and capabilities compactly. Safe region metadata may reject a region only when it proves that no member can satisfy the query. Enumerate only geographic regions that could intersect the search radius and keep only the best small number of results instead of sorting every match. Ranking must retain full unrounded distance, then queue time, then locker ID.

A balanced point index is typically O(N log N) preprocessing and O(N) memory; a suitable grid can be O(N) to build. Query cost should track visited regions/candidates plus small top-result maintenance. Exact designs still have dense worst cases; candidates should acknowledge them rather than claim guaranteed constant time.

## Why naive approaches fail

A global scan is not credible at 8M lockers times 1.2M requests. Planar degrees are not the distance contract. Naive longitude rectangles can fail around ±180° or near poles. Ranking by rounded distance changes valid ordering. Duplicating the whole snapshot for every capability subset is wasteful. Sorting every eligible result wastes work when the limit is at most 20. Approximate pruning without a proven lower bound can silently remove the exact answer.

## Subtle traps

The fixture includes identical-coordinate San Francisco lockers, a nearby maintenance locker, an active zero-slot Oakland locker, lockers on both sides of the date line, and a near-pole locker. Size strings must not be compared lexicographically. Capability matching is exact token containment. Boolean values must not be accepted as integer query fields. Row order is not meaningful. Ranking uses raw distance, not the emitted rounded meter value.

## Evaluator-only checks

- Shuffle locker rows and capability order; output must remain unchanged.
- Add several eligible lockers at identical coordinates with different queue times and IDs.
- Add closer maintenance, offline, zero-slot, undersized, and missing-capability decoys.
- Check exact-token behavior such as `cold` versus `cold-storage`.
- Search across the international date line with a small radius and query very near a pole.
- Create two lockers whose exact distances differ while both round to the same output meter; ordering must still use exact distance.
- Test a locker exactly on the radius boundary and another just outside it.
- Duplicate and permute query capability requirements.
- Feed booleans, numeric strings, non-finite coordinates, malformed JSON, then a valid line; later lines must still run.
- Cross-check optimized results against a simple exhaustive reference on randomized small snapshots.
- Use a synthetic large fixture to expose accidental whole-snapshot work per query.

## Alternative defensible designs

Conservative spherical/geographic tiling with exact post-filtering and metric-tree search are strong alternatives. A production geospatial library would also be reasonable outside this dependency-free starter. Approximate nearest-neighbor methods are defensible only if the candidate explicitly states which exact radius/top-k guarantees are surrendered. An LLM should not be in the critical geographic decision path.

## Likely AI-agent failure modes

Typical failures are producing a polished full scan that only passes the tiny fixture, using planar distance, forgetting date-line behavior, ranking on rounded distance, comparing sizes as strings, substring-matching capabilities, building an index that still visits every point, or trusting approximate pruning without proving it cannot lose a valid answer.

## What should be discovered from the data

The fixture shows that this is not just nearest-point lookup: business filters invalidate attractive points; two lockers share coordinates; date-line and polar cases are present; and invalid query records are mixed with valid records. The candidate should inspect these before choosing a design.

## Recommended prioritization

A strong 60-minute sequence is: restate exact eligibility/ranking, verify the starter, build a correctness core, add reusable geographic search state with conservative pruning, test adversarial boundaries, then explain scale and worst cases. A partially optimized exact design with a clear next step is stronger than a complex index whose pruning cannot be defended.

## Walkthrough inspection points

Inspect how size/capabilities are modeled; whether pruning is provably safe; whether exact great-circle distance remains the final check; whether date-line/polar correctness follows from the representation; whether only a bounded best-result set is maintained; deterministic ties; query versus snapshot error handling; boundary tests; memory assumptions at 8M lockers; dense-radius worst cases; and whether AI-generated code was verified rather than blindly accepted.
