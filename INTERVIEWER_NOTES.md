# INTERVIEWER NOTES — POST-PRACTICE ONLY

These notes reveal intended structures, traps, and hidden checks. Do not expose them before the practice session.

## Intended underlying problem structure

This is a typo-tolerant prefix-search problem over a very large immutable string set with three levels of exact deterministic ranking:

1. choose the best qualifying prefix for one searchable surface;
2. choose the best surface for one canonical term across canonical text and aliases;
3. choose the global top `limit` canonical terms.

A strong exact design naturally partitions by locale and indexes normalized searchable surfaces by character prefix. During query evaluation, carry a dynamic-programming edit-cost row while traversing only plausible prefix states. At a prefix state, the cell for the full query gives the number of edits required to transform the query into that prefix. Branches whose row cannot get within the edit budget can be pruned.

Because `max_edits <= 2`, any qualifying prefix length differs from the query length by at most 2. The search therefore only needs to consider a narrow depth band around the query length; it should not walk arbitrarily deep strings just to decide whether their prefix matches.

The harder production issue is descendant retrieval. A qualifying prefix node can represent millions of completions. Enumerating the entire subtree and sorting is not credible. Strong production answers maintain subtree metadata and expose a lazy best-first iterator (or another exact bounded top-k structure) so only enough descendant surface records are materialized to establish the first few unique canonical terms. Fixed small cached top lists are useful but are not exact by themselves when duplicate terms/aliases can occupy many positions; the candidate should identify that limitation if proposing them.

## Strong solution approaches

### Interview-correct core

For a 60-minute implementation, the following is strong if clearly separated from the production optimization discussion:

- Build one normalized character-prefix index per locale.
- Insert canonical and alias surfaces; terminal records retain `term_id`, original display surface, canonical/alias flag, alias ID, and normalized surface length.
- For a query, traverse reachable prefix states while maintaining one edit-cost row per state and prune states beyond budget.
- Track qualifying prefixes in the allowed depth band.
- Enumerate candidate descendant surfaces for those prefixes, compute the exact best evidence per term, then apply the final comparator and top `limit`.
- Add tests that validate correctness independently from the small fixture.

This may still be too expensive on extremely hot prefixes; award correctness but reserve scalability points unless the candidate adds or convincingly designs bounded descendant retrieval.

### Production-oriented exact refinement

Use immutable per-node aggregate metadata that exposes the best unseen descendant under the local ranking dimensions. Expand descendants lazily with a small heap/frontier rather than recursively enumerating every terminal. Merge candidate streams from all qualifying prefix states, update the best evidence per `term_id`, and continue until the frontier's best possible unseen rank cannot beat the current kth unique term. Deduplication across aliases and across multiple qualifying prefix states must happen by canonical `term_id`.

Compact integer node IDs, packed child tables, string interning, and term/surface IDs matter for the 1.25 GB target. A naive JavaScript object per character/node will likely exceed the production memory budget even if the algorithm is asymptotically sound. It is fine for the interview implementation if the candidate says so explicitly.

Alternative exact structures are acceptable, including finite-state representations, compressed radix structures, or specialized deletion-neighborhood indexes, provided the candidate preserves the exact prefix and ranking contract and can defend memory growth.

## Complexity discussion

Let `m` be normalized query length, `e <= 2` the edit budget, and `S` the set of reachable indexed prefix states after pruning.

A prefix-index traversal with one edit row per visited state is roughly `O(|S| * m)` in the straightforward implementation and uses `O(m)` row memory per active traversal frame/state if rows are not all retained. The practical value comes from pruning and the narrow depth band `m-e .. m+e`, not from scanning the full locale.

Candidate enumeration must be discussed separately. A recursive walk of every descendant under a hot qualifying prefix can dominate query cost and violate the latency target. A lazy top-k descendant frontier should scale with the number of expanded candidate nodes/surfaces needed to prove the top result set, rather than subtree cardinality.

## Why naive approaches fail

- Full scan: tens of millions of surfaces per keystroke.
- Compare only to a prefix with exactly `query.length` characters: misses valid insertions/deletions where the best qualifying prefix length differs by 1 or 2.
- Treat alias surfaces as independent suggestions: emits one canonical term multiple times.
- Stop at the first qualifying prefix on a surface path: can choose too many completion characters when a deeper prefix ties on edits.
- Cache only the ten most popular descendants per prefix: duplicate aliases/terms or completion-length tie-breaks can make the exact top ten require looking deeper.
- Sort all qualifying surfaces: wrong unit (surface rather than canonical term) and too much work.
- Use JavaScript string `.length` for Unicode code-point lengths: surrogate pairs count incorrectly.
- Run fuzzy correction first and exact prefix lookup second using one corrected string: may discard multiple equally valid correction paths needed for exact ranking.

## Subtle traps / hidden checks

1. **End-boundary insertion:** query `wireles`, surface prefix `wireless` is one insertion; implementations that compare only equal lengths fail.
2. **End-boundary deletion:** query `wirelesss`, prefix `wireless` is one deletion.
3. **Best deeper prefix:** construct a surface where two prefixes both require one edit; the deeper prefix must win because it leaves fewer completion characters.
4. **Non-empty prefix rule:** a one-character query with edit budget 1 must not match every term merely by deleting the query into the empty prefix.
5. **Alias dedupe:** one canonical term matching through multiple surfaces appears once with the best surface evidence.
6. **Canonical-vs-alias tie:** canonical wins only after edits and completion tie. An alias with fewer completion characters beats canonical even when edit count ties.
7. **Popularity ordering:** popularity outranks completion length in final term ranking.
8. **Inactive term:** an exact alias match for an inactive term still returns nothing.
9. **Locale isolation:** identical surface in `en-US` and `fr-FR` is not cross-searchable.
10. **Identical normalized surfaces across different terms:** both may be returned and term ID resolves the deepest tie.
11. **Unicode code points:** hidden data includes an emoji and composed/accented characters; normalization and completion lengths must use code points.
12. **Full-width normalization:** NFKC should make full-width Latin characters match ordinary Latin characters.
13. **Conflicting alias replay:** same alias ID with changed term/text must fail snapshot validation.
14. **Row-order independence:** shuffle terms/aliases and confirm the same output.
15. **Hot prefix scale discussion:** query `w` with `max_edits=2` should trigger a discussion about frontier explosion and bounded descendant retrieval even if the fixture is small.

## What should be discovered from the checked-in data

- `a-001` appears twice identically and must deduplicate.
- `t-002` has both canonical and alias surfaces beginning with `wireless`; a surface-oriented implementation can duplicate it.
- `t-009` looks like a strong exact completion for `wireless charging p` but is inactive.
- `q-007` requires one substitution between plain `e` and accented `é` after NFKC/lowercasing; normalization does not strip accents.
- `q-bad` demonstrates per-query invalid handling without aborting the run.

## Expected fixture-level behavior worth spot-checking

- `q-001` should rank `t-002` before `t-001`, then `t-008` among the obvious `wireless...` candidates because edits tie and popularity is the next final term criterion. `t-002`'s best matched surface may be its shorter alias `wireless buds` because completion length is compared before canonical-vs-alias source.
- `q-002` should return the Bluetooth aliases, with `t-002` ahead of `t-001` by popularity.
- `q-008` should resolve with an empty list because the only exact `wireless charging p...` canonical term is inactive.
- `q-009` should resolve successfully with an empty list rather than being treated as an invalid locale.

Do not require candidates to memorize these outputs; use them as inspection points.

## Alternative defensible designs

- A deletion-neighborhood index can be reasonable because the edit budget is tiny, but the candidate must reason carefully about insertions/substitutions, prefix boundaries, duplicate generated keys, index blow-up, and top-k completion retrieval.
- A compressed radix index reduces node overhead but makes edit-state transitions across multi-code-point edges more complex.
- A finite-state automaton intersection approach can be excellent but is well beyond what should be required in one hour.
- An approximate spell-correction or embedding stage is acceptable only as a candidate generator if a deterministic verification/ranking stage restores the exact contract. A purely model-driven result is not appropriate for the critical path under the stated latency and exactness requirements.

## Likely AI-agent failure modes

- Generates a full scan with a textbook edit-distance function because the fixture is tiny.
- Names a sophisticated index but still recursively enumerates every descendant once a fuzzy prefix matches.
- Forgets that aliases collapse to canonical terms.
- Applies canonical preference before completion length.
- Uses surface popularity (which does not exist) rather than canonical-term popularity.
- Uses `.length` everywhere and misses Unicode code-point semantics.
- Mutates the supplied normalizer inconsistently between load and query paths.
- Adds broad tests for examples but no adversarial boundary test.
- Over-optimizes the data structure before first producing a correct comparator and term-reconciliation model.

## Recommended prioritization for the hour

1. Restate normalization, matching, surface selection, and final ranking separately.
2. Get a correct bounded matching core working on a few adversarial strings.
3. Deduplicate and rank by canonical term correctly.
4. Add tests for end insert/delete, alias dedupe, inactive terms, and one tie.
5. Only then optimize query narrowing/index traversal.
6. Use remaining time to articulate how hot-prefix descendant retrieval would be made lazy/bounded in production.

## Walkthrough inspection points

Ask the candidate to show:

- the exact comparator/key for prefix evidence, surface/term evidence, and final terms;
- how one alias/canonical term cannot appear twice;
- where a branch is pruned under the edit budget;
- a test in which the best qualifying prefix length is not equal to query length;
- the work done for `max_edits=0` versus `max_edits=2`;
- what happens for a one-character hot query;
- why the implementation is deterministic after shuffling fixture rows;
- the specific part they would replace or compact first to meet the production memory/latency target.
