# POST-PRACTICE ONLY — SkyParcel Interviewer Notes

**Evaluator-only. Never copy or reference these notes, hidden tests, or this file in candidate materials or candidate-branch history.**

## What the candidate should discover

This is a **static spatial stabbing / point-in-polygon-with-holes query problem**, constrained by region, time, altitude, exact integer geometry and a top-k ranking. The deceptive part is that the small file looks like a simple per-zone loop, but a 300k-zone / 4M-vertex snapshot and 12M/day workload invalidate a complete scan for each waypoint. The catalog is static during a run, so substantial preprocessing is justified. In particular, the `bay_core` exemption area, `bay_donut` hole, reverse winding of `bay_reversed`, concavity of `bay_priority`, and diagonal edges in `sf_triangle` demand exact geometry rather than rectangle checks.

## Strong approach A: precomputed region + spatial index

1. Load and deduplicate zone IDs before emitting any response. Preserve the domain's structural validation; upstream guarantees geometric ring topology, not necessarily a convenient winding direction.
2. For every zone compute its axis-aligned bounding box and exact **twice-net-area** as an arbitrary-precision integer: `abs(sum(x_i*y_(i+1) - x_(i+1)*y_i) for outer) - sum(abs(...) for each hole)`. Using twice-area avoids fractions. Never assume all rings share orientation; account for every hole. Verify the net area is positive if adding a defensive topology check.
3. Partition first by `region`; build an R-tree/packed bounding-volume hierarchy/STR-like index over zone bounding rectangles in each partition. A static packed AABB tree built by median splits (or STR bulk loading) is feasible without dependencies. Store lightweight IDs and bounds in internal nodes; avoid copying full vertex arrays into nodes.
4. At query time get conservative bbox candidates for `(x,y)`; filter by half-open time and altitude bounds; run exact point-in-outer and point-in-holes only for survivors; finally sort eligible results by `(-priority, twice_net_area, zone_id)` and select top `limit`. Returning 3 IDs does not mean only 3 candidates need examination unless a provably safe upper-bound/rank scheme is used.
5. A point on any outer edge is inside; a point on any hole edge is excluded. Test point-on-segment exactly using integer cross product equality plus inclusive min/max coordinate bounds. For interior, use a half-open crossing convention with integer cross-product comparisons; ensure reversed edges and vertex crossings are handled consistently. A winding-number method can also work. Avoid floating point and divide-by-zero for horizontal edges.

**Complexity:** let `N` be zones, `V` total vertices, `C` conservatively located boxes and `V_C` vertices examined after cheap attribute filters. Bulk building a balanced spatial structure is around `O(N log N + V)` (or `O(N log N)` for bounding-box sorting plus `O(V)` to scan vertices), memory `O(N+V)`; typical indexed queries `O(log N + C + V_C + C log limit)` or `O(log N + C + V_C + C log C)` if sorting. The **worst case is still O(N+V)** when all zones have overlapping bounds and all pass filters. Region isolation, broad-node tracking, cheap time/altitude gating and hotspot-aware partitions improve the distribution, but no exact index can guarantee constant time under pathological overlapping polygons without far greater preprocessing. Ask candidates not to claim a hard p95 from unbenchmarked Python.

## Strong approach B: grid cells / adaptive bucketing

A sparse spatial hash can map small bboxes to intersecting grid buckets, with large/broad zones stored separately and checked per query. Adaptively subdivide hot cells; ensure each query examines every required bucket and broad-zone list. A naive grid that inserts a zone in **every** cell of a huge bounding box can use explosive memory. A candidate can use bounding volume hierarchy or a hybrid to avoid that. An external geospatial engine would be defensible only if startup, exact boundary semantics, deterministic ordering, costs and lack of credentials are addressed. LLM-based semantic matching alone is unsuitable for required exact coordinates; hybrid candidate retrieval is permitted only with a no-false-negative guarantee and exact confirmation.

## Subtle traps / hidden checks

- Boundary: outer edge/vertex INCLUDED; hole edge/vertex EXCLUDED. An inward hole boundary is not a restriction match.
- Concavity: the interior of `bay_priority`'s notch is outside despite lying within its bbox. Holes may have winding opposite to outer or equal; orientation must not affect membership.
- Time and altitude are **both half-open** at the upper endpoint. A zone starting at time 100 is present at exactly 100. A point altitude of 200 is absent from a `[0,200)` band and present in `[200,500)`.
- Exact integer arithmetic: large coordinates give cross products beyond signed 64-bit in large-vertex polygons; using Python `int` avoids overflow. Floating point can silently misclassify points near sloped edges or misrank equal areas.
- Ties sort case-sensitive zone IDs lexicographically, not row order or whichever zone was found first. Smaller area means **net area** after holes, not bbox or outer area. Priority always precedes area.
- Identical replays collapse; conflicting zone IDs invalidate the **entire snapshot** before printing any result. Bad query JSON, booleans, invalid IDs/limits should produce a line error without suppressing later valid lines. Duplicate request IDs are independent.
- A query with region absent from the catalog is valid with no matches. Time/altitude filtering and region isolation must not accidentally overapply to other queries.
- Horizontal/vertical, diagonal, collinear intermediate vertices, polygon clockwise/counterclockwise and large negative coordinates should each have explicit tests.
- One `point-in-polygon` shortcut for outer and holes must distinguish on-edge from strictly inside; using a library default `contains` often excludes the outer boundary and mishandles hole boundaries.

## Suggested hidden verification

Use `python3 -m unittest discover -s evaluator_tests -v` **after** the candidate implements the feature. The tests deliberately fail on the supplied stub. Extend coverage with a small, independently implemented exact reference and randomized simple polygons. Include performance runs with several hundred thousand small disjoint rectangles plus a few broad polygons, then a deliberately overlapping worst case. Never give candidates the hidden fixtures or notes beforehand.

A robust differential test checks a few hundred randomly generated rectangles and triangular zones against a slow reference using exact integer calculations, repeated across random queries, including all four boundaries. The fixture should also test stable results under randomized catalog row order and varying query order, plus the same request ID appearing more than once. Do not equate success of the starter's structure tests with matching correctness.

## Likely AI-agent failure modes

A single prompt often generates a full scan, `shapely` dependency despite no extra packages, float-based ray intersection that double-counts vertices, bbox-only membership, a rank formula using `priority - area`, no explicit hole-edge exclusion, sorting before filtering, or a grid that duplicates broad zones across millions of cells. AI output may include a superficially impressive benchmark that never exercises dense overlap. Verify the diff, input validation and integer boundary checks; seek candidate-owned explanations.

## 60-minute interviewer cadence

- 0–8 min: inspect fixtures, paraphrase contract, enumerate six traps, articulate feasibility of full scan.
- 8–18 min: decide on data model/index and an exact membership routine; discuss how to handle broad zones and complexity.
- 18–40 min: implement a working vertical slice; check outer/hole boundaries, time, altitude and rank.
- 40–52 min: implement conservative spatial candidate pruning, add focused correctness and performance checks.
- 52–60 min: test, explain measured behavior, discuss dense/worst-case cost, startup/memory and production extension.

During walkthrough ask: Why does the index never omit a zone? How are boundary crossings handled without floats? Why does net area use absolute oriented sums? What happens with 30k overlapping bounding boxes? How would you verify the 15ms p95 claim? How can a different valid algorithm or AI-assisted workflow still meet the exact contract?
