# SignalWatch — Interviewer Notes

**POST-PRACTICE ONLY. DO NOT OPEN BEFORE PRACTICING.**

## Intended structure and strong solution

This is a **multi-pattern sequence matching** task over normalized ASCII word tokens, with a static latest-revision snapshot and multi-tenant routing. A strong approach builds a separate token-keyed **Aho–Corasick automaton** per tenant (or a shared automaton keyed by tenant), with trie transitions, failure links and output pattern-ID lists. Stream each event's tokens once through the automaton. On each match, record the signature ID's first start index (`current_token_index - phrase_token_length + 1`); never record it again for that request. Keep matching IDs independent even when phrases are equal. Sort unique matched records by `(-priority, first_token, signature_id)` and return the first `limit`. `total` must count all unique matching IDs before limiting.

If duplicated phrases are very common, map each distinct normalized phrase to a tuple of signature IDs and priority records at one terminal, preserving duplicates by ID. Build and traverse the token automaton for distinct phrases, then expand to IDs only as necessary for exact total and ranking. Output-link traversal or cached suffix outputs avoids quadratic copying when many patterns are suffixes of others; discuss output size versus number of repeated occurrences. Correct first positions can be set on the first arrival at each pattern, since tokens stream in order. A performance-conscious implementation may avoid repeat expansion once IDs are marked seen. Aho build is roughly O(total tokens across distinct patterns + automaton links + materialized output links); event matching is O(event tokens + emitted occurrences) expected with amortized failure traversal, plus O(M log M) ranking for M distinct matching IDs, or top-k selection O(M log k) plus exact count. Memory roughly O(total pattern tokens + associated IDs), notwithstanding high fanout and Python object overhead.

Alternative defensible approaches: tokenize and build a fixed-depth per-tenant inverted n-gram index keyed by token tuples of length 1..8; for each event generate every contiguous n-gram once and gather exact IDs. O(8*T + matched-record collection), memory O(total distinct phrase tokens) assuming efficient tuple hashing, and avoids automaton complexity. Hash collisions must be verified if using hashes rather than tuples. This alternative is **fully creditworthy** when its scale/memory estimates are credible; there is no single mandated architecture. Search all phrases/event using regex or `if phrase in text` is not valid at scale and is semantically wrong around punctuation and token boundaries. An LLM-only classifier cannot guarantee exact positions and deterministic results.

## Nuanced correctness and hidden inspection cases

1. `CARD-payment declined` tokenizes to `card payment declined`; it matches both that phrase and `payment declined` starting at different token offsets.
2. `payment--declined` matches `payment declined`, but `paymentdeclined` does not; `code404` differs from `code 404`.
3. A phrase `account account` matches overlapping occurrences of a repeated token stream. `first_token` is minimum, not most recent.
4. Duplicate IDs with a higher `retract` are inactive even if an old upsert occurs last in CSV. Distinct IDs using one phrase both count.
5. `limit:0` returns empty matches and still reports all unique matching IDs.
6. Priority dominates position, then earliest position dominates ID. Case-sensitive IDs (`A` before `a`, `sig-10` before `sig-2`).
7. A tenant sees no patterns from another tenant even when phrase text is identical. Unknown tenant returns invalid, not `ok` with no matches.
8. Empty lines in JSONL produce invalid responses; each physical line counts and a duplicate event ID does not imply a cache hit.
9. `true`, `1.0` and `"1"` do not pass integer validation; tabs/newlines/non-ASCII characters inside `text` are invalid.
10. Catalog row order can be shuffled with a repeated same-revision delivery; conflicting same revision or a cross-tenant signature ID fails the whole catalog before output.
11. If `limit:1`, hidden cases still check `total` when hundreds of patterns match. Watch for code that stops at the limit.
12. Catalogs containing signature phrases sharing all but their last token, or 8-token identical-prefix phrases, stress per-event throughput.

## Why naive / common AI-agent implementations fail

- Scanning every phrase with substring or regex per event: O(P*T), tenant confusion, punctuation/substring false positives, not viable at 900k signatures.
- Building a trie but scanning from every token without an explicit max-length cap: can be O(8*T), still defensible because max phrase length is fixed at 8; if candidate has bounds and exact contracts, reward this design. A naive unbounded trie restart at every token risks bad cases.
- Counting occurrences rather than distinct IDs, failing duplicates, losing earliest position, sorting only by priority, doing top-k before counting total.
- Using Unicode regex `\w` or lower() on arbitrary non-ASCII input instead of the specified ASCII token rules.
- Forgetting to apply current revision or trusting CSV order; mishandling retractions and bad even-superseded rows.
- Treating output paths as unique phrases rather than IDs, collapsing distinct IDs sharing phrase.
- Trusting an AI-generated matcher without constructing an independent tiny brute-force test oracle.

## What to discover in fixtures

`NORTH` includes shared phrases, nested phrases, duplicate deliveries, highest-revision replacement and retraction, same-priority ties, and punctuation-sensitive token matches. `SOUTH` has a phrase also found in `NORTH`, which should not leak. `LAB` includes its own unrelated patterns. `events.jsonl` includes valid and invalid events and duplicate event IDs. `invalid_only.jsonl` is intentionally adequate for a green baseline before the candidate implements screening.

## Interview prioritization and walkthrough

Suggested schedule: 0–8 minutes inspect files/data and state invariants; 8–15 derive matching/ranking plan and complexity; 15–40 implement the index and evaluator; 40–52 targeted tests, run fixture and fix edge cases; 52–60 explain tradeoffs and risks. On walkthrough, ask the candidate to point to where latest revisions are chosen, how multiple signatures with identical phrase are counted, how an overlapping token match is found, how `first_token` is chosen, and why the solution scales beyond sample fixtures. Ask how they independently verified a high-priority later match against a lower-priority earlier one. Inspect stdout cleanliness, zero limit behavior, bounded RAM, and retry/reordered catalog stability.

A complete solution is not required in 60 minutes; rank decisions, verified partial functionality and a realistic next-step plan. The rubric deliberately caps brute-force solutions that ignore production constraints.
