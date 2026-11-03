# POST-PRACTICE ONLY — BatchGuard grading rubric (100 points)

**Use only after the candidate's 60-minute exercise.** Score observable behavior, tests and defended engineering decisions. Assign partial credit within each category, then apply the stated cap. A pretty UI with a happy-path CSV parser is not a strong result.

| Area | Points | What earns full credit |
| --- | ---: | --- |
| Feature decomposition and scope management | 8 | Identifies receipt, per-sample validity, per-lot staleness, derived quality, and browser recovery as distinct concerns; prioritizes working vertical slice. |
| CSV and domain correctness | 24 | Correct UTF-8/BOM/quoted CSV handling, exact header contract, numeric/unit validation, decimal precision, correct ordered sample corrections, event replay/conflict behavior and reliable per-sample error isolation. |
| Revisions, dedupe and batch integrity | 20 | Per-lot stale rejection without blocking others; no partial mutations of rejected lots; no-op revision behavior; request-key replay/collision semantics and concurrent same-key safety. |
| Derived QC logic | 12 | Product-specific inclusive thresholds, minimum distinct sample counts, correction replacement, authoritative readiness in both endpoints, deterministic sorted offenders. |
| Frontend and API integration | 12 | File and paste workflow, truthful per-lot/per-sample diagnostics, server-authoritative list/detail refresh, preserved data and key after uncertain delivery, stale browser response resistance. |
| Verification and edge cases | 12 | Existing tests stay green; targeted tests for boundary values, malformed/colliding IDs, ordering, newer corrections, stale/closed mixed lots, exact replay, client error states and fixture behavior. |
| Scale and design choices | 6 | Efficient lookup/merge without repeated full-sample scans, bounded payload/row handling, explainable complexity and latency tradeoffs. |
| Code quality and walkthrough | 6 | Clear responsibilities, precise contract/error naming, maintainable changes, smoke-tested UI and candid defense of omissions/AI assistance. |
| **TOTAL** | **100** | |

## Scoring limits
- **Maximum 60** if only straightforward single-lot CSV ingestion works, even if the UI looks complete. In particular, no meaningful stale state, replay protection or correction handling means the solution is happy-path only.
- **Maximum 55** if all prior samples are rescanned for each CSV row, ties rely on input order, or independent samples and lots cannot be isolated.
- **Maximum 50** if a correct-looking submission overwrites a newer lot revision, duplicates delivery, or reports client-derived readiness as authoritative.
- **Maximum 40** if the pre-existing lot search, details or note updates are broken.
- **Maximum 35** if the feature is a nonfunctional mock or only conceptual code.

Full credit is possible with an alternate architecture that genuinely satisfies the contracts and scalability constraints; score behavior and explanation, not conformity to these notes.
