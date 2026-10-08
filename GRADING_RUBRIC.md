# POST-PRACTICE ONLY — Grading Rubric

ThermoTrace. **Total 100 points.** Evaluate behavior, not code volume.

- Feature correctness: 16 (preview, commit, evidence, lifecycle).
- Temperature semantics: 25 (retries 5, equal instants 4, quality/gaps 5, strict bounds 5, contiguous threshold 6).
- Backend state: 18 (authoritative decisions 4, sticky hold 4, revision/no-op 5, stale and invalid writes 5).
- Idempotency: 13 (key collision 4, replay original 4, delayed safety 3, concurrent duplicates 2).
- Browser: 10 (controls 5, stale response 3, recovery 2).
- Testing: 10 (edge cases 5, HTTP/races 3, baseline 2).
- Code/complexity: 5.
- Tradeoff explanation: 3.

**Caps:** hardcoded/UI-only <=30; any-spike or disjoint-duration <=50; happy path ignoring gaps/retries/staleness <=60; lost note revision behavior <=65. Inspect SH-101, SH-102, SH-105 and an in-flight stale commit.
