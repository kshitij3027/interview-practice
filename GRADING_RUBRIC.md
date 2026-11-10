# POST-PRACTICE ONLY — FlagHarbor grading rubric (100 points)

| Dimension | Points | Expectations |
|---|---:|---|
| Domain correctness / targeting semantics | 26 | Off/deny/allow precedence; plan/region gates; 0/100 and stable monotone percentage assignment; reason codes and cross-tenant isolation. |
| Mutations, concurrency and retry semantics | 22 | Atomic revision checks, no-op behavior, dataset revision, original immutable receipt, replay before stale check, key collision, rejected requests never reserve keys. |
| API integration and validation | 14 | Contract/status/error envelopes, offset/limit/whole-org counts, strict policy validation, bounded input handling, safe ID scoping. |
| Browser behavior and UX | 14 | Usable editor, audience pagination/explanations, state handling, safe retry with frozen intent, conflict recovery, async selection guards. |
| Edge cases / adversarial input | 10 | Duplicate/invalid enum arrays, cross-tenant overrides, disabled explicit allow, malformed percentages, empty cohorts, old notes and concurrent requests. |
| Testing and verification | 8 | Preserved baseline, focused domain+HTTP regression tests, documented runnable smoke checks, verified save→audience→note sequence. |
| Code quality and reasoning | 6 | Clear layering, bounded complexity, restrained changes, tradeoff explanation. |
| **Total** | **100** | |

## Calibration and score caps
- Happy-path only with hard-coded target IDs or unstable random percentage: **cap 60** even with working UI.
- No meaningful revision/idempotency protection: **cap 62**.
- Cross-tenant disclosure or mutations affecting another org: **cap 55**.
- Backend-only work with no credible UI integration: **cap 72**.
- Broken starter functionality or failing baseline tests: subtract as appropriate; major regression generally **cap 65**.
- A working deterministic eligibility endpoint with good tests but limited UI may still earn partial credit; do not reward a fabricated demo.

Award points for observed behavior plus a defensible walkthrough, not for guessing a preferred code structure. No specific hash function or dependency is mandatory if the stable monotone property is demonstrated and the method is portable across restarts.
