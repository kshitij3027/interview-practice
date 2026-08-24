# INTERVIEWER_NOTES — RoutePolicy

**POST-PRACTICE ONLY. DO NOT SHOW TO THE CANDIDATE DURING THE EXERCISE.**

## Intended underlying structure

This is primarily a hierarchical pattern-matching/indexing problem, not an LLM problem. The strongest deterministic solutions usually organize rule patterns by path segments so request lookup explores only compatible literal/wildcard states instead of scanning every rule. A trie-like or automaton-like representation is natural, but do not require that exact implementation if the candidate proposes another structure with equivalent correctness and query bounds.

The single `**` token creates the core reasoning difficulty because it may consume zero or many request segments. A correct resolver must preserve full-path semantics and avoid duplicate candidate emission when multiple matching paths through the matcher reach the same rule.

Tenant/region scope and time windows are secondary filters that can be incorporated into indexing to different degrees. There is no requirement to fully optimize every dimension in 60 minutes; a strong candidate should identify which one dominates production cost and justify the tradeoff.

## Strong solution approaches

### Approach A: hierarchical matcher + candidate filtering

Build an index over path-pattern segments. Each node can have literal children, a `*` child, and a `**` transition/state. Attach terminal rule references only to pattern endpoints. At query time, walk request segments while tracking compatible states; memoize `(node, request_index)` or otherwise prevent repeated work. `**` can branch into consuming zero or one-more segments. Because rule patterns contain at most one `**` and request depth is capped at 32, the state space can be tightly bounded for typical rule sets.

After producing candidate rule IDs, apply tenant, region, validity-window filters and compute one precedence key. Keep only the best rule.

### Approach B: split patterns around `**`

Partition rules into literal/`*` patterns and patterns containing `**`. For the latter, store the prefix before `**` and suffix after it. Index compatible prefixes and suffixes separately, then intersect/validate candidates. This can reduce wildcard-state branching and make zero/many-segment semantics explicit. It is more complex to implement cleanly in an hour but can be highly defensible.

### Approach C: coarse scope/path buckets + exact matcher

A candidate may first partition rules by `(tenant-or-*, region-or-*, first literal-ish segment, depth class)` and then run an exact wildcard matcher on a small candidate set. This can be acceptable if they can demonstrate that bucket sizes remain controlled at production scale. It is weaker than a direct hierarchical matcher if broad wildcard rules produce giant buckets.

## Complexity expectations

For a trie/automaton-style matcher, startup should be roughly proportional to total pattern segments plus rule metadata. Query time should depend on request depth and the number of compatible wildcard/literal states/candidates, not on all 1.5M rules. With request depth capped at 32 and only one `**` per pattern, a candidate should be able to explain why typical state exploration is small, while acknowledging pathological rule sets with huge numbers of identical wildcard shapes.

A plain Python object-per-node trie may violate the 512 MB target at 1.5M policies; strong candidates may call this out even if they still implement it for the interview fixture. Compact integer IDs, arrays, interning path strings, compressed adjacency, or scope partitioning are plausible production evolutions.

## Why naive approaches fail

- Full scan of 1.5M rules per request cannot plausibly hit p95 <5 ms.
- Pre-expanding `*`/`**` into all possible concrete paths is unbounded and memory-prohibitive.
- Regex-compiling every rule still leaves the candidate scanning all regexes unless additional indexing is introduced.
- Sorting all matches after discovery is unnecessary; maintain the best precedence key incrementally.
- Treating `**` as only one-or-more segments fails zero-segment cases.
- Treating matching as prefix matching incorrectly accepts patterns that do not consume the full request path.

## Hidden checks

1. `payments/**/refund` matches both `payments/refund` and `payments/a/b/refund`.
2. `**` matches a one-segment path and a deep path.
3. `payments/**/chargeback` must not match `payments/a/chargeback/extra`.
4. `visa*` is literal and must not match `visa` or `visa123`.
5. Higher priority beats specificity; specificity only breaks equal priority.
6. Equal priority/literal/wildcard counts are then resolved by exact tenant, then exact region, then rule ID.
7. A rule active exactly at `valid_from` matches; exactly at `valid_to` does not.
8. Exact duplicate `rule_id` rows deduplicate; conflicting duplicates fail before resolver construction.
9. Multiple matcher paths must not duplicate a rule or change deterministic precedence.
10. A broad wildcard rule must still be considered alongside narrow exact rules.
11. Input order shuffled repeatedly yields identical winners.
12. A synthetic fixture with many irrelevant rules should not cause request time proportional to the full rule count.

## Subtle traps in the supplied fixture

- `r-zero-segment` exists specifically to force zero-segment `**` reasoning.
- `r-literal-star` checks that wildcard syntax is token-based, not substring-based.
- `r-acme-us-visa-promo` expires on September 1, so the same logical path has different winners in August vs September.
- `r-global-block` has very high priority and should beat more specific lower-priority routing rules when it matches.
- The duplicated `r-global` line is intentional and valid.

## Alternative defensible designs

A candidate could use generated regexes inside indexed buckets, a compact finite-state matcher, prefix/suffix indexing for `**`, or another retrieval structure. Grade the observable semantics and scaling argument rather than whether they chose the evaluator's preferred data structure.

An LLM or heuristic should generally not be necessary because matching and precedence are exact. If the candidate proposes one, require them to explain how deterministic correctness is preserved. An LLM might have value outside the resolver—for example, helping customers author rules or diagnose conflicts—but it should not replace exact policy evaluation.

## Likely AI-agent failure modes

- One-shot implementation scans all rules because the fixture is small.
- Converts patterns to regex and overlooks the production lookup problem.
- Implements `**` greedily with no backtracking/zero-length case.
- Uses a generic recursive matcher that can revisit the same states exponentially.
- Sorts by an incorrect specificity key or places specificity ahead of priority.
- Parses timestamps as naive datetimes.
- Builds a huge nested Python-object trie and claims it fits 512 MB without measurement.
- Writes tests only for the eight supplied requests and misses adversarial semantics.

## What the candidate should discover from the data

They should notice overlapping global/tenant/region rules, identical duplicate rows, a bounded promotion window, a literal segment containing `*`, and patterns where `**` must match both zero and multiple segments. These observations should influence test selection before implementation is considered complete.

## Recommended 60-minute prioritization

- **0–10 min:** inspect fixtures, restate matching/precedence, identify scale bottleneck, choose representation.
- **10–35 min:** implement candidate discovery/matching and winner selection.
- **35–50 min:** add focused correctness tests for wildcard and precedence edge cases.
- **50–60 min:** run end-to-end fixture, discuss complexity/memory/pathological cases, and tighten defects.

A candidate who has a correct literal/`*` path but incomplete `**` handling at minute 40 may still recover by narrowing scope and explicitly testing zero/multi-segment semantics rather than expanding into architecture polish.

## Walkthrough inspection points

Ask the candidate to explain:

- the maximum work their matcher can do for one 32-segment request;
- how they prevent `**` from causing repeated/exponential states;
- where scope/time filtering occurs and why;
- the exact precedence key and sign/direction of each field;
- why their production memory estimate is credible;
- what benchmark they would run to validate the 5 ms target;
- what happens if 500k rules are all `**` at the same priority.
