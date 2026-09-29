# Interviewer Notes — EvalBoard Regression Gate

POST-PRACTICE ONLY — DO NOT OPEN BEFORE COMPLETING THE EXERCISE

## Intended solution structure

A strong solution usually separates three concerns:

1. Build an index over relevant observations keyed by runId/caseId, keeping the winning observation with the exact comparator: higher numeric attempt, then later parsed timestamp instant, then lexicographically larger observationId.
2. Put comparison logic in a pure function that receives suite/cases/baseline/candidate data and returns deterministic metrics, gate diagnostics, and case regressions.
3. Keep approval at a mutation boundary that first resolves request-key idempotency, then checks current suite revision/status/dataset, recomputes the gate against the current approved baseline, and only then changes approvedRunId plus revisions.

For N relevant observations and C suite cases, a strong comparison is roughly O(N + C + C log C) because p95 requires sorting covered latencies. Nested C-by-N matching is not appropriate for the stated scale.

Frontend response ownership can be handled with request-generation counters, explicit suite/candidate identity checks, or AbortController plus a final identity check.

## Exact metric guidance

Coverage: coveredWeight / totalWeight.

Quality: sum(qualityMilli * weight) / coveredWeight.

Latency: sort covered latencyMs values and select index ceil(0.95 * n) - 1.

Cost: sum(costMicrousd) / coveredCount.

Prefer integer cross-multiplication for gate truth:
- coverage >= 95%: coveredWeight * 100 >= totalWeight * 95.
- latency <= +20%: candidateP95 * 100 <= baselineP95 * 120.
- cost <= +25%: candidateCostSum * baselineCount * 100 <= baselineCostSum * candidateCount * 125.
- quality can be compared as rationals after subtracting the 15-point allowance.
- critical case passes at exactly baseline minus 40 and fails below that.

Displayed rounded values should not drive approval.

## Why naive approaches fail

- observations.find inside every case loop becomes quadratic on large suites.
- Taking first or last fixture row makes the result depend on input order.
- String-sorting attempts makes attempt 10 sort before attempt 2.
- Comparing timestamp strings rather than parsed instants mishandles offset-equivalent times.
- Treating missing/error cases as quality zero changes the specified quality metric; they should lower coverage instead.
- Ignoring weights gives the wrong coverage and quality.
- Calculating pass/fail in the browser makes approval tamperable and stale.
- Reusing old comparison metrics during approval misses a changed baseline.
- Performing stale validation before idempotency lookup breaks retries after a successful mutation because the successful mutation changed the revision.

## Hidden checks

1. Multiple observations include attempts 2 and 10; numeric ordering must win.
2. Equal attempts use offset-equivalent recordedAt instants; observationId breaks the final tie.
3. Shuffle all observation rows: comparison output and gate result must not change.
4. Exactly 95% weighted coverage passes.
5. Exactly 15 milli-points quality drop passes.
6. Exactly +20% p95 latency passes.
7. Exactly +25% average cost passes.
8. Critical case exactly -40 passes; -41 fails.
9. Candidate error on a critical case fails both coverage as applicable and the critical-case gate.
10. Zero covered candidate returns explicit safe metrics, not NaN/Infinity/crash.
11. run-support-olddata is rejected for dataset mismatch.
12. Comparison on a paused suite may be allowed; approval must fail without mutation.
13. Delayed approval followed by an owner-note update returns stale with no approved-run change.
14. Retrying the same request key/payload after successful approval returns the original success even though revisions have since changed.
15. Same request key with different candidate or observed revision fails without mutation.
16. Slow Compare A followed by fast Compare B cannot repaint B.
17. Navigate to another suite while approval is in flight; old response cannot replace the new workspace.

## Defensible alternatives

- Recompute everything on approval, or cache comparison results only if cache identity is immutable and approval still verifies the current approved baseline/current suite state.
- Rational helper objects, BigInt cross-multiplication, or carefully bounded integer arithmetic are all defensible.
- AbortController, monotonic request IDs, or explicit tuple matching are all fine for stale-response protection.
- Idempotency storage can be global or per suite, but must retain normalized logical payload and original response for the process lifetime.

## Likely AI-agent failure modes

- One large route handler duplicates comparison logic in the approval route.
- UI comparison works but approval trusts the comparison response.
- Floats and rounded display metrics are reused for gate decisions.
- Error observations are counted as zero-quality covered cases.
- Max recordedAt is chosen while attempt priority is ignored.
- Request-key storage records only that a key was seen, so exact retry response cannot be reproduced.
- Buttons are disabled during requests but old fetch responses still commit stale state.
- Existing note no-op/stale revision semantics are accidentally changed.

## What the supplied data should reveal

- run-support-cand-43 has a retry plus an error case and a meaningful regression on the high-weight refund-policy case; simplistic averaging can make it look safer than it is.
- run-support-cand-44 is a cleaner successful-path candidate.
- run-support-olddata exists to exercise dataset mismatch.
- moderation-triage is paused and has a candidate with an error on a critical case.
- Other suites provide small independent examples so the implementation should not hard-code the support suite.

## Recommended 60-minute prioritization

0–8 min: inspect fixtures, store, routes, revision boundary, and frontend state.
8–25 min: build effective-observation indexing plus pure metric/gate function and focused tests.
25–38 min: add comparison API and minimal UI with stale-response protection.
38–50 min: add approval mutation, current-state recomputation, stale revision handling, and idempotency.
50–57 min: reconcile UI after success/stale and exercise delay races.
57–60 min: run all tests/build and prepare the tradeoff explanation.

## Walkthrough inspection points

Ask the candidate to show:
- the effective-observation comparator and asymptotic complexity;
- how exact threshold comparisons are represented;
- why missing/error affects coverage but not quality average;
- where approval recomputation/current-baseline validation happens;
- why idempotency lookup happens in the right order;
- how a slow response is prevented from updating newer frontend state;
- which tests preserve the original note/revision behavior.
