# SourceMark — Interviewer Notes

**POST-PRACTICE ONLY — EVALUATOR MATERIAL. Do not open during candidate's timed exercise.**

## Intended underlying structure

The problem is a **minimum-cardinality hitting set** with cardinality at most three. Each positive mix is a constraint that at least one chosen supplier lot belongs to it; each negative mix forbids every contained lot. Once forbidden lots are removed, represent each eligible lot by a bitmask of which distinct positive mixes it hits. Find the lexicographically smallest *set of lot IDs* whose union covers every positive mix, minimizing size before lex ordering. Ambiguity means a second distinct set of the same minimum size, not a larger feasible set. A declared positive empty mix is impossible. All selected lots must be at the requested site.

## Strong solution approaches

1. Validate and ingest the immutable catalog once. Keep reverse mix membership plus optional lot-to-mix indexes. Deduplicate deliveries without conflating different lot IDs or hiding declared empty mixes.
2. Parse a request completely; union lots belonging to negative mixes to form forbidden candidates. For each distinct positive mix assign one of at most 40 bit positions. Build eligible lot coverage for lots touched by positive mixes, excluding lots with zero coverage; they cannot improve a nonempty optimum.
3. If there are no positives, the unique optimum is the empty set. If any positive mix has no remaining eligible lot, return `no_match`. Test possible source counts in ascending order: one, two, then three, stopping at the first size that has a solution. Ensure the chosen IDs are sorted, and compare sorted arrays lexicographically.
4. For one source check full coverage; for two sources find complementary coverage masks using inverted positive indexes, mask grouping, complementary/superset lookups, or carefully bounded candidates. For three, branch on an uncovered positive mix with few surviving choices and prune when remaining sources cannot cover necessary evidence. Preserve two distinct witness sets where ambiguity could exist, and preserve lex order across alternative branches.
5. Grouping identical coverage patterns is helpful under skew, but retain at least two smallest distinct IDs for ambiguity; a single ID per pattern is not enough. Dense dynamic programming over `2^P` masks can be good for small positive count `P`, but `P=40` makes a dense table prohibitively large. Sparse memoization, bitsets and hybrid search are defensible if correctness is preserved.

Catalog ingestion is `O(L+M+E)` time and space for lots, mixes, memberships. Per-request construction is proportional to the memberships touched by selected mixes, with complexity of optimized bounded search depending on remaining unique coverage masks and branching. Trying every triple among 200,000 lots is `O(L^3)` and not credible. The general hitting-set problem is NP-hard; bounded maximum of three supports exact specialized search, but adversarial worst cases still demand honest complexity discussion. Reuse signatures/cache for frequently repeated mix combinations.

## Expected fixture discoveries

- `LOT-A01` appears twice identically in the lot catalog; `MX-O1,LOT-A01` appears twice in membership. They contribute one source/membership, not two.
- `MX-O0` and `MX-R0` are legal empty mixes.
- `case-01` => unique minimum `["LOT-A02"]` after accounting for the negative O5 mix.
- `case-02` => unique minimum `["LOT-A01"]` after O2 eliminates A02 and A04.
- `case-03` => unique minimum `["LOT-A06"]`.
- `case-04` => `no_match` because a positive empty mix cannot be explained.
- `case-05` => `ok`, sources `[]`, count `0`, ambiguous `false`.
- `case-06` => minimum `["LOT-A01"]`, count `1`, ambiguous `true` (A02 and A03 are equally small).
- `case-07` => minimum `["LOT-A01","LOT-A07"]`, count `2`, ambiguous `true` (A02,A07 also works).
- `case-08` => unique minimum `["LOT-B02"]`.
- `case-09` => `no_match` at cap 1; raising to 2 yields several optimal sets.
- `case-10` has contradictory readings of the same mix and is `invalid_query`, while `case-11` has harmless duplicate readings. Later lines test malformed JSON, unknown mix, wrong site, unknown site, JSON boolean cap, blank line and repeated independent request ID.

## Hidden checks and subtle traps

- With no positives and cap zero, return the empty unique optimum regardless of negatives. With positives and cap zero, no match.
- Overlapping positive/negative mixes can remove all candidates from a positive mix, yielding `no_match`, not `invalid`.
- A unique feasible two-source set must remain unambiguous even if many three-source feasible sets exist.
- Distinct lot IDs with **identical coverage masks** yield distinct solutions and can create ambiguity; repeated *rows* do not.
- Choosing one lot per positive mix greedily can produce more sources than necessary, or violate negatives.
- Comparator is (number of lots, sorted case-sensitive array), not ingredient label, first CSV row, cost, or coverage count.
- A valid request may contain a 128-character ID; other IDs max 48. Python `True` is an `int` under `isinstance`, so use exact type checking for max_sources.
- All mixes of a valid request must be at its site. Query isolation does not permit different-site lots. Parse errors are isolated; catalog errors cause zero scan output.
- Case-sensitive IDs, sparse mix memberships, duplicate memberships, empty mixes, and reordering of CSV must all be harmless.
- Compare the optimized solver with a separate `itertools.combinations` oracle on many randomly constructed tiny fixtures (e.g. <=8 lots) to detect wrong lex winner, false ambiguity and missed solutions.

## Likely AI-agent failure modes

A one-shot agent may enumerate combinations across the entire site; stop at the first feasible result; conflate different lot IDs with identical masks; allocate a dense `2^40` array; ignore negative evidence; treat duplicate rows as distinct; assume every mix is nonempty; allow cross-site members; or mistake the green baseline for implemented customer logic. Algorithms that prune by coverage must prove they cannot remove lex-smaller or second-optimal witness sets.

## Prioritization and walkthrough inspection

Suggested time allocation: 8 minutes for inspecting data and semantics, 12 for negative filtering and coverage representation, 25 for exact bounded search with tie/ambiguity, 10 for adversarial verification, and 5 for explaining tradeoffs. Inspect whether (1) negative lots are excluded; (2) global minimum cardinality is proved; (3) ambiguity counts distinct *minimum* sets; (4) three-source cases are considered; (5) there is a credible scale story; (6) positive empty mixes fail correctly; (7) CLI error isolation is preserved; and (8) correctness is tested independently. An appropriately justified alternative solver is acceptable if it is runnable with the standard-library starter and meets the observable contract.
