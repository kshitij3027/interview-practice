# QueueCraft — HARD One-Hour AI-Assisted Interview

## Context
An enterprise compliance platform routes open customer cases to qualified reviewers. Reviewers have limited capacity, certifications, and region restrictions; some reviewer/customer pairs are prohibited by separation-of-duty rules. The current severity-first/fastest-reviewer prototype can make locally sensible choices that block a better batch-wide plan.

## Supplied data
- fixtures/reviewers.csv: reviewer_id, region, pipe-separated certifications, max_cases. Region GLOBAL may serve any case region.
- fixtures/cases.csv: case_id, customer_id, region, pipe-separated required_certifications, positive severity.
- fixtures/estimates.csv: sparse case_id/reviewer_id/predicted_minutes pairs. A pair is assignable only if an estimate exists. Exact duplicate pair rows are harmless; conflicting values are invalid.
- fixtures/conflicts.csv: reviewer_id/customer_id pairs that may never be assigned. Exact duplicate rows are harmless.
- fixtures/batches.jsonl: independent batch_id, case_ids, disabled_reviewers requests. Duplicate IDs inside either array behave as one ID.

## Goal
For each valid batch, choose case-to-reviewer assignments. A pair is feasible only when the reviewer is not disabled, an estimate exists, region matches or reviewer region is GLOBAL, all required certification tokens are present exactly, no reviewer/customer conflict exists, reviewer max_cases is respected, and a case is assigned at most once. Cases may remain unassigned.

## Plan quality
Among all feasible plans, apply these objectives in order:
1. maximize total assigned severity;
2. then maximize assigned case count;
3. then minimize total predicted_minutes;
4. then choose the lexicographically smallest assignment sequence after sorting assignments by case_id and comparing (case_id, reviewer_id) pairs.

Results must be independent of input row order, JSON array order, map iteration order, or process hash behavior.

## Observable behavior
A planned result contains batch_id, status=planned, assignments, unassigned, assigned_severity, assigned_count, and total_predicted_minutes. Sort assignments by case_id and unassigned lexicographically.

Unknown case IDs produce only that batch as invalid with reason unknown_case. Unknown disabled reviewer IDs produce reason unknown_reviewer. Later batches still run.

## Acceptance criteria
- Process batches independently; no capacity carries across batches.
- Duplicate IDs in batch arrays behave as one.
- Certification matching is exact token set containment; aml does not equal aml-advanced. Empty requirements are valid.
- GLOBAL is special only on reviewers.
- Conflicts override otherwise-valid eligibility.
- Missing estimate means ineligible; do not infer a time.
- Capacity is consumed per assigned case.
- A valid case with no feasible reviewer is simply unassigned.
- Global optimality matters: a locally fastest or severity-first greedy choice can be wrong.
- Exact duplicate estimate rows deduplicate; conflicting duplicates fail dataset validation.
- Duplicate static reviewer/case IDs, unknown references in estimates, unknown reviewers in conflicts, non-positive numeric fields, empty identifiers, malformed token lists, or empty reviewer region fail dataset validation.
- Empty case_ids is a valid planned batch with zero totals.
- Diagnostics go to stderr; stdout remains JSONL.

## Production constraints
Design for about 40k reviewers, 3M case records, 30M sparse estimates, 2M conflicts, and 5k batches against one snapshot. Typical batch size is 200–2,000 cases; incident batches may reach 10k. Reviewer capacity is usually 1–8 but may reach 100. Most cases have 3–30 candidate estimates. Memory budget: 1.5 GB. Target: p95 under 500 ms for a typical batch after preprocessing.

Do not enumerate complete assignments, rescan all 30M estimates per batch, or rely on a local greedy rule. Preprocessing reusable indexes is allowed. Heuristic/approximate designs are defensible only if you identify which exact guarantees they give up.

## Expected deliverable
Implement AssignmentPlanner.plan_batch() in assignment/planner.py and supporting code as needed. Add focused tests and be ready to explain eligibility, capacity, objective ordering, a concrete greedy failure, deterministic ties, and startup/per-batch complexity.

## Run / verify
No third-party dependencies are required.

    bash scripts/test.sh
    bash scripts/build.sh
    bash scripts/verify.sh

After implementation:

    python3 queuecraft.py plan --reviewers fixtures/reviewers.csv --cases fixtures/cases.csv --estimates fixtures/estimates.csv --conflicts fixtures/conflicts.csv --batches fixtures/batches.jsonl

## Scope
In scope: immutable snapshot loading, validation, sparse eligibility, independent batch planning, deterministic output, and scaling reasoning. Out of scope: clock-time scheduling, live presence, distributed coordination, persistence, authentication, and UI.

## 60-minute instruction
You have 60 minutes and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the repository and fixtures yourself, identify why the problem is global rather than local, implement incrementally, run verification, and be ready to defend the design.
