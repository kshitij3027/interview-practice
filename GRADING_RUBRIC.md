# ProofSpan — Evaluator scoring rubric (100 points)

**EVALUATOR ONLY · POST-PRACTICE ONLY · Do not copy to the candidate branch.**

This is a one-hour AI-assisted, customer-facing engineering assessment. Score the candidate's actual behavior and reasoned tradeoffs, not whether they name or copy a particular algorithm. Exactness under the documented contract is mandatory regardless of deterministic, heuristic, LLM-assisted or hybrid implementation. A hybrid can receive full design credit if exact computation governs the required numeric outputs and model components have defensible scope, latency and cost.

| Dimension | Points | Evidence |
| --- | ---: | --- |
| Problem understanding and decomposition | **12** | Reads real fixtures, distinguishes evidence *revision* from active interval, identifies vendor vs probe identity, separates snapshot preparation from independent audits, restates four exact output metrics. |
| Technical design and data representation | **20** | Appropriate representation of latest records, overlapping same-vendor evidence and time boundaries; sound precomputation or indexing for many queries; explains why the representation is correct. |
| Functional correctness | **22** | Correct active vendor counts across scopes and times (9), correct covered duration (4), earliest gap (3), clipped longest gap (3), contiguous gap count (3). |
| Complexity, scale and resource reasoning | **14** | Derives initialization and query complexity, handles skew and up to 1e12 timestamps without dense allocation, quantifies memory and likely bottlenecks, addresses throughput target. |
| Critical edge conditions | **12** | Interval inclusivity/exclusivity, simultaneous transitions, duplicate vendor attestations, retractions/corrections, holes/touching gaps, empty scopes, window clipping, deterministic responses. |
| Verification and test discipline | **10** | Writes targeted cases beyond starter tests, uses a small independent oracle or manual checks, verifies CLI and failure contracts, examines adversarial boundary cases, reviews AI-generated code. |
| Implementation quality and operational robustness | **4** | Readable maintainable code, minimal dependencies, safe integer handling, isolated invalid JSONL, atomic catalog errors, practical failure handling. |
| Explanation and tradeoff defense | **6** | Can explain logic and invariants without line-by-line prompts, defend deterministic/heuristic/LLM-hybrid alternatives, discuss latency, memory, correctness and future engineering priorities. |
| **Total** | **100** | |

## Calibration and caps

- **Strong (85–100):** Exact answers on evaluator checks; handles multi-probe vendor deduplication, arbitrary clipped windows, sparse extremes and replay semantics; credible design for production volume; good tests and walkthrough.
- **Good (70–84):** Correct core and most traps; bounded inefficiency or a few edge issues with an explicit improvement plan.
- **Partial (45–69):** Functional for small fixtures but omits some dimensions or does not defend scale.
- **Shallow ≤55:** A brute-force scan of all observations for every audit with no credible scalable alternative, even if small-fixture outputs are correct. **Cap at 55** if every query iterates all observations and no precomputed/indexed query plan is identified.
- **Shallow ≤60:** Counts probes or observation rows rather than distinct vendors, even if the remainder is polished. **Cap at 60** for this fundamental semantic error.
- **Failure ≤40:** Returns plausible but fabricated numbers/LLM guesses with no exact validation, ignores revisions or fails most functional checks.

Don't reward merely using an AI SDK or penalize not using one. No extra credit for external services. A candidate can gain substantial reasoning credit for an exact but incomplete implementation with a well-scoped plan and oracle verification.
