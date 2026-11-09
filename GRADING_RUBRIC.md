# POST-PRACTICE ONLY — VaultScope Grading Rubric (100 points)

Evaluator material. Do not show before the 60-minute interview.

| Area | Points | What earns strong credit |
|---|---:|---|
| Customer problem decomposition | 12 | States effective policy, time, latest-revision, tenant isolation, witness constraints; identifies real ambiguity and asks productive questions. |
| Algorithm and representation choice | 22 | Distinguishes group containment reachability from grants; handles cycles, minimal witness and deterministic tie breaking; designs useful indices/preparation and justifies alternatives. |
| Functional correctness | 25 | Exact direct/group policy applicability, deny dominance, `none`, complete witness paths, correct revocations and half-open times, consistent JSON contract. |
| Complexity and scalability | 14 | Understands preprocessing/query tradeoffs, heavy fan-out, repeated user/time queries, per-resource filtering, memory bounds and correctness of caches. |
| Adversarial edge cases | 12 | Cross-tenant safeguards, shared descendants, cycles, ties, duplicate/conflicting revisions, timestamp boundaries, deleted policies, malformed input and recovery. |
| Self-directed verification | 8 | Runs baseline and targeted adversarial tests, checks outcomes rather than only structure, uses differential tests or explicit examples and fixes failures. |
| Code quality and maintainability | 4 | Readable modules, purposeful interfaces, separation of parsing and core reasoning, no obscure magic or unchecked assumptions. |
| Walkthrough and tradeoff defense | 3 | Can explain paths, conflict rules, complexity and where AI-generated code was checked, with an honest remaining-risk assessment. |
| **Total** | **100** | |

## Rating gates

- A happy-path-only implementation (flat groups/direct allows) caps at **55/100**, even if polished.
- Brute force repeated full-policy/full-membership scans that ignore the published scale cap at **55/100**.
- Any implementation that ignores deny dominance or treats group cycles as errors caps at **60/100**.
- Fabricated explanation chains, cross-tenant authorizations, or unsound time caching are critical correctness failures; substantial deduction under correctness/edge-case categories.
- Grading favors working, verified increments and a clear complexity explanation over untested speculative optimizations.
