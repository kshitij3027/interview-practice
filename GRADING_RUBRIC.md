# POST-PRACTICE ONLY — SkyParcel Interview Grading Rubric (100 points)

**Evaluator material: never place on candidate branch or in its ancestry.** Grade the code actually demonstrated in 60 minutes and the explanation. This rubric permits deterministic, heuristic, LLM-based, or hybrid approaches but never grants correctness points for plausible yet wrong outputs.

| Category | Points | Evidence |
| --- | ---: | --- |
| Problem decomposition and requirements | 12 | Articulates exact region, time, altitude, outer/hole, boundary, rank, output contracts; distinguishes upstream topology guarantees from required structural validation. |
| Exact lookup correctness | 28 | Correct inclusion and exclusion (12); independent time/altitude/region filtering (6); ranking by priority/net area/ID and limit (7); deterministic results and response format (3). |
| Algorithm / data representation | 20 | Uses or credibly implements region partitioning and conservative candidate pruning (10); exact per-candidate membership checks (6); handles dense/broad zones without an explosive index (4). |
| Edge-case behavior | 14 | Hole boundary and outer boundary (4); concave and winding-reversed shapes (3); negative/large coordinates and arithmetic exactness (3); replayed/conflicting IDs, malformed per-line requests and duplicate query IDs (4). |
| Performance and complexity analysis | 12 | Explains preprocessing and index memory (4); expected query complexity versus dense worst case (4); startup costs, instrumentation, and 2GB/15ms tradeoffs (4). |
| Verification | 8 | Adds targeted correct-answer tests and uses fixture inspection (4); adds randomized differential or purposeful adversarial/performance tests (4). |
| Walkthrough and AI-assisted engineering | 6 | Can defend chosen deterministic/heuristic/LLM/hybrid approach, review AI-generated code and errors, and prioritize within time (6). |
| **Total** | **100** | |

## Calibration and caps

- An always-empty stub scores at most **12**, regardless of tests passing.
- A happy-path implementation that scans every zone for every query, without meaningful indexing or a technically concrete scale-up design, **cannot score above 55**. Correctness on small fixtures alone does not overcome this cap. A full scan plus a sophisticated and justified indexing plan may earn some scalability points, but still must not be presented as meeting the production latency target.
- A solution that uses floating-point approximations or probabilistic filters **without exact confirmation** cannot score above **60**, because the customer contract requires exact classification and ranking. Probabilistic *candidate generation followed by complete exact verification* is acceptable only if zero false negatives can be argued.
- Systematic incorrect hole/boundary behavior caps at **65**, and unverified one-shot AI code caps at **65**, even if the general approach is strong.
- Give full credit to a justified nontraditional architecture if observable outputs are exact and runtime claims credible. Do not reward invoking an LLM by default. Interviewers should examine the candidate's reasoning, tests, and understanding rather than count files or lines of code.

## Guidance on 60-minute scoring

A solid 70–79 typically has an exact baseline, targeted edge-case tests, and at least a working conservative index with realistic worst-case discussion. An 80–89 needs robust geometry, correct sorting and filters, clean error isolation, and measurable indexing benefits. A 90+ solution demonstrates careful scale and skew analysis, integer-exact edge handling, and differentiated correctness/performance tests. Do not silently change the hidden contract to make a particular approach pass.
