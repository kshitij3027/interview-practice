# WaveSend — Grading rubric (evaluator only, 100 points)

| Dimension | Points | What earns full credit |
|---|---:|---|
| End-to-end feature and API | 15 | Preview and dispatch endpoints, credible operator UI, correct status codes and payload contracts, sound default behavior. |
| Consent reconciliation and safety | 20 | Safe event-ID deduplication, per-scope effective-time/source selection, global/SMS separation, invalid/conflicting evidence isolation, opt-out veto and unknown-consent suppression. |
| Phone grouping and frequency decisions | 15 | Strict canonicalization, cross-record and cross-segment veto, representative choice, rolling 24-hour window, cross-campaign ledger, sorting and cap order. |
| Dispatch correctness and revision semantics | 15 | Server-bound preview, exact stale validation, idempotency with parameter mismatch protection, provider partial results, exact one-step revision increments and zero-mutation failures. |
| Frontend interaction and race recovery | 10 | Functional preview/dispatch, auditable reasons, partial results, stable controls on error, delayed-response protection, selection changes and authoritative refresh. |
| Verification and debugging | 10 | Focused tests for happy/negative/boundary scenarios, HTTP testing, documented observed outcomes, and starter regression passes. |
| Complexity and scalability | 8 | Pre-indexed group/event/history data, bounded work per request, explicit complexity analysis and sensible memory tradeoffs. |
| Code quality and decomposition | 4 | Clear domain/API/client responsibilities, legible validation, no hidden mutation in preview, maintainable state contracts. |
| Walkthrough and judgment | 3 | Can explain ambiguous semantics, implementation choices, AI use, remaining risks and time prioritization. |
| **Total** | **100** | |

Grading guidance: happy-path wiring that sends a list but omits effective-time consent, group-level veto or 24-hour semantics scores **at most 55/100**. A superficially correct UI with no stale/idempotency safety scores **at most 60/100**. Brute-force rescanning all events/history per contact under production constraints caps at **60/100** even when small fixtures pass. Ignoring opt-outs or duplicate phone safety is a major functional defect; do not award full backend correctness points. Failure to keep original note-editing behavior green loses regression and integration credit. An incremental, tested server-first solution that openly discusses missing UI/race handling may score above a polished-looking untested implementation.
