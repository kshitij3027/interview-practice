# TransitShield — Evaluator Grading Rubric (100 points; POST-PRACTICE ONLY)

Evaluate the candidate's actual solution and explanation, not a required technology. Deterministic, heuristic, LLM, and hybrid proposals can earn credit for justified tradeoffs; however, an approximate or probabilistic method cannot receive exact-correctness credit without meeting the observable contract.

| Dimension | Points | Standard |
| --- | ---: | --- |
| Customer problem decomposition | 12 | Distinguishes original-window filtering, three independent global generalizations, per-group k threshold, whole-group suppression, feasible releases, and final optimization. Identifies invariants and assumptions before coding. |
| Algorithm / data representation choice | 18 | Exact plan selection, reusable grouped evidence, indexing/preprocessing, defensible costs across different k/windows, justified deterministic vs heuristic vs LLM or hybrid tradeoffs. |
| Correctness and optimization | 24 | Considers all 36 alternatives or proves pruning safe; exact group counts, suppression and feasibility, integer loss, globally minimum tuple, sector isolation, empty/no_release semantics. |
| Scalability and complexity | 15 | Explains preprocessing and per-query cost for 1.2M records / 70k queries, 768MB, time-window repetition, skew, worst-case access, memory growth and credible design choices. |
| Edge cases, validation and isolation | 12 | Time boundaries, k equality, all-suppressed rejection, zero weights/penalties, ties, retries/conflicts, malformed queries, unknown sectors and IDs. |
| Verification and testing | 10 | New focused/adversarial tests, independently derived outputs, negative cases, input-order invariance, and measured or reasoned performance checks beyond smoke tests. |
| Code quality / maintainability | 5 | Clear separation, legible names, deterministic results, sensible errors, light setup and reproducible commands. |
| Walkthrough / AI use and defense | 4 | Explains code, risks and limits, time-budget decisions, checks AI-generated snippets and defends tradeoffs. |
| **TOTAL** | **100** | |

## Calibration

- Happy path using trip scans for all 36 plans **per query**, few tests, and no credible strategy for scale: **cap at 58/100** even if fixture outputs look right.
- Any release of groups smaller than k, partial-group suppression, or mistaken filtering after generalization: **cap at 55/100**.
- An approximate/LLM guess presented as guaranteed exact optimum cannot get full correctness credit. A rigorous hybrid may.
- Reward an exact well-verified working slice plus an honest scale plan over unexplained one-shot complexity.
