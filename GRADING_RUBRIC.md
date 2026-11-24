# Grading rubric — POST-PRACTICE ONLY

Score out of 100. Evaluate observable behavior, inspect the implementation and run tests. Award partial credit within each category; do not reward a particular architecture merely for matching the notes.

| Category | Points | Evidence |
| --- | ---: | --- |
| End-to-end functional correctness | 15 | Valid report request returns all selected meters/hours (5); report totals and coverage are useful (5); CSV corresponds to reviewed report (5). |
| Backend/domain semantics | 25 | Correct highest-sequence selection independent of order (6); duplicate collapse and equal-sequence conflicts (5); rejected winner and missing endpoints (4); epoch and monotonicity checks (4); exact integer differences, null/zero and weighted totals (6). |
| API, scope and integration | 10 | Strict UTC window and revision validation (4); site/filter/order contract and structured errors (3); consistent JSON/CSV contract and proper escaping/content type (3). |
| Frontend workflow | 15 | Window and search controls plus clear report (6); coverage/partial usage and unknown reasons (4); downloadable CSV using reviewed parameters and revision (5). |
| Failure handling and edge cases | 20 | Atomic revision/snapshot boundary and stale export rejection (7); no-op and unrelated-site edits do not invalidate (3); delayed responses, changed selection/inputs and retry/regeneration without silent replacement (6); no-data/empty selection/boundary cases (4). |
| Verification and tests | 10 | Targeted semantic tests (4); API stale export and baseline regression tests (4); demonstrated execution/debugging of the app (2). |
| Code quality and scale | 5 | Understandable separation, avoids repeated full-feed scans, discusses tradeoffs and limitations (5). |
| **Total** | **100** | |

A happy-path-only implementation that ignores major correction, missing-data and stale-export semantics is capped at 60. A report with unsafe cross-site leakage or a CSV that silently exports a different revision is capped at 55. A backend-only solution may receive credit for domain and API behavior but not unimplemented browser functionality. Score what runs, not what is promised. Do not deduct twice for the same omission when applying a cap.
