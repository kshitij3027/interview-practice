# POST-PRACTICE ONLY — MergeGuard Interviewer Notes

Evaluator-only. Do not expose this file before or during the exercise.

## Intended underlying structure

This is an incremental equivalence-class problem with persistent incompatibility constraints.

A strong deterministic approach uses a disjoint-set/union structure for group membership plus per-component metadata for:

- current canonical member;
- component size / optional member container for queries;
- the set of other current components that this component is forbidden to merge with.

The key difficulty is that the forbidden relation lives between **groups**, not merely between the endpoints named by the incoming link. When groups merge, their conflict metadata must be merged and all neighboring groups that referred to the old representative must be redirected to the new representative.

A strong implementation typically combines union-by-size/rank and path compression for membership with small-to-large movement of member/conflict metadata. The exact representation can vary.

## Strong solution outline

1. Parse all records and normalize/deduplicate symmetric separation pairs.
2. Initialize each record as its own group.
3. Attach each initial separation as a symmetric conflict relation between singleton groups.
4. For a link `(a,b)`:
   - resolve the current group representatives;
   - if equal, return accepted/no-op with current canonical metadata;
   - if either representative appears in the other's conflict set, reject without mutating state;
   - otherwise choose a deterministic/size-aware surviving representative and merge the groups;
   - combine member state and canonical metadata;
   - merge conflict sets, rewriting each neighboring group's back-reference from the losing representative to the surviving representative;
   - ensure no self-conflict remains.
5. For a query, resolve the representative, return its canonical member and lexicographically sorted members.

The mutation sequence matters. Candidates who start rewriting neighbors before they know the merge is valid can violate atomicity if their conflict check is incomplete.

## Expected complexity

With path compression and union-by-size/rank, representative lookups are effectively near-constant amortized.

If conflict/member metadata is merged small-to-large, each metadata entry moves only logarithmically many times across the lifetime of the process. A useful high-level bound is approximately:

- membership operations: near `O(alpha(N))` amortized;
- conflict metadata maintenance: total movement around `O(S log N)` across merges for `S` separation incidences, depending on representation;
- query representative lookup: near constant amortized;
- materializing a full member list is necessarily `O(group_size log group_size)` if sorted on demand, or can trade memory/update cost to maintain sorted structures.

A candidate need not state a perfectly formal bound, but should recognize that rescanning all separations or both full groups on every link is not credible.

## Why naive approaches fail

- Rebuilding connected components after each link scans too much static/history data.
- Checking only `(left,right)` against the separation set misses forbidden pairs between other members of the two groups.
- Keeping separations only at record level and scanning all members cross-product on each merge can be catastrophic for 100k-member groups.
- Updating group membership by rewriting every member's representative on every merge produces quadratic behavior on long chains unless size-aware.
- An LLM-based merge decision cannot guarantee the exact safety invariant and is unnecessary because the supplied links/separations are authoritative.

## Subtle traps / hidden checks

1. **Non-endpoint conflict:** `crm:100` linked with `support:44`; `crm:101` linked with `support:45`; separation exists between `support:44` and `support:45`. A later link between another pair across those groups must be rejected.
2. **Reversed duplicate separation:** the fixture contains both `crm:100,billing:901` and its reverse. It should normalize once.
3. **Atomic rejection:** snapshot/query both groups, attempt a forbidden merge, then verify all members and canonical IDs are unchanged.
4. **Rejection is local:** after a rejected merge, perform a different valid link involving one group and verify it succeeds.
5. **Same-group retry:** repeat an accepted link; group size and canonical result must not change.
6. **Canonical update:** joining a group with a higher-quality member must update canonical deterministically.
7. **Canonical tie:** equal quality uses earlier timestamp, then lexicographic ID.
8. **Long adversarial chain:** merge singleton groups in an order that punishes naive representative/member rewrites.
9. **Large conflict fan-out:** merge a group carrying many separation relationships and ensure neighboring conflict references are updated correctly.
10. **Self-conflict cleanup:** after metadata merge, the surviving group must never retain itself in its forbidden set.

## Alternative defensible designs

A candidate can use component IDs distinct from DSU roots, hash-based member sets, intrusive linked membership, or other representations if correctness and complexity are justified.

Maintaining canonical metadata incrementally is preferred, but recomputing canonical from the smaller/merged member set may receive partial credit if the candidate explicitly discusses the large-group cost.

For queries, maintaining unsorted members and sorting only when queried is defensible because member-list output itself is large. Maintaining an always-sorted tree is also defensible but changes update/memory costs.

A database-backed or distributed design may be a sensible production extension, but is out of scope for the coding hour.

## Deterministic vs heuristic / LLM decision

The authoritative inputs already specify exact link and separation facts, so the core reconciliation engine should be deterministic. An LLM might be useful upstream to *propose* candidate links from fuzzy names, but those proposals would need separate confidence/review semantics and must not weaken MergeGuard's exact constraints.

Do not penalize a candidate merely for discussing an LLM/hybrid option. Penalize using nondeterministic model output as the enforcement mechanism for separation safety.

## Likely AI-agent failure modes

- One-shot generation of a basic union-find that ignores separations between existing groups.
- Storing separations by original record IDs and doing an `O(|A|*|B|)` cross-product check on each merge.
- Mutating parent pointers before validating the conflict and then trying to roll back incompletely.
- Correct group roots but stale conflict-set references after representatives change.
- Forgetting deterministic canonical tie-break order.
- Candidate-visible tests pass because they only exercise loaders, giving false confidence that the core is complete.

## What the candidate should discover from the fixture

The fixture contains two clusters whose endpoints can look harmless while an internal member pair is separated. It also contains duplicate/reversed separation rows and repeated links. A good candidate inspects these before coding and explicitly calls out that the safety test is component-level.

## Recommended 60-minute prioritization

- **0–10 min:** inspect fixtures/requirements; state invariants and representation.
- **10–30 min:** implement group membership, canonical metadata, basic safe merge.
- **30–45 min:** implement/repair component-level conflict metadata and atomic rejection.
- **45–55 min:** add adversarial tests for indirect conflict, no-op retry, canonical behavior, and post-rejection validity.
- **55–60 min:** run fixture end-to-end and explain complexity/pathological cases.

## What to inspect during walkthrough

Ask the candidate to trace one accepted merge and one rejected merge through every state structure. Then ask:

- How would this behave if a component has 100k members but only two conflicts?
- What if it has 10 members and 500k conflicts?
- Which entries move when two large conflict sets merge?
- Can a rejected operation alter path-compression state, and is that semantically acceptable?
- What is the unavoidable cost of returning every member in a 100k-member query?
- Where, if anywhere, would AI add value without weakening the hard invariant?
