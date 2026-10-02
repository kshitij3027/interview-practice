# QueryMend — HARD One-Hour AI-Assisted Problem-Solving Interview

## Customer / business context

A large marketplace uses a typeahead box on product-search pages. Merchants and shoppers often type only the first few characters of a phrase, and mobile users frequently make one or two small typing mistakes. The existing service linearly scans every searchable phrase for each keystroke. It is correct on a tiny catalog but becomes unusable when the catalog and request rate grow.

You are given one immutable suggestion snapshot containing canonical search terms plus curated aliases. Build the in-process suggestion resolver used by the API tier.

The customer-facing requirement is simple: return the best canonical suggestions for a partially typed query, even when the typed text contains a small number of single-character mistakes. The engineering challenge is to preserve the exact ranking contract without scanning the full snapshot for every request.

## Supplied data

### `fixtures/terms.csv`

Columns:

- `term_id` — globally unique canonical term identifier.
- `locale` — exact locale such as `en-US` or `fr-FR`.
- `text` — canonical display text.
- `popularity` — non-negative integer business score; larger is more popular.
- `active` — `true` or `false`.

Only active terms may be returned. Canonical text is also a searchable surface for that term.

### `fixtures/aliases.csv`

Columns:

- `alias_id` — globally unique logical alias identifier.
- `term_id` — canonical term this alias points to.
- `text` — additional searchable surface.

Aliases inherit the locale and active state of their canonical term. Exact duplicate rows with the same `alias_id` are harmless replay deliveries and behave as one alias. Reusing one `alias_id` with different contents is invalid.

Different terms may legitimately have identical normalized canonical or alias text.

### `fixtures/queries.jsonl`

Each line contains:

- `request_id` — unique request identifier.
- `locale` — exact locale to search.
- `text` — typed text.
- `max_edits` — integer `0`, `1`, or `2`.
- `limit` — positive integer at most `10`.

Queries are independent and read-only. Output must preserve query-file order.

## Text normalization

The starter repository provides the normalization helper used by both fixture loading and queries. Use that exact behavior rather than inventing a second normalization path.

Normalization performs Unicode NFKC normalization, lowercasing, trimming, and collapsing runs of whitespace to one ASCII space. The normalized value must be non-empty.

All matching and completion lengths are measured in Unicode code points after normalization, not raw UTF-16 code units or bytes.

## Matching semantics

For one searchable surface, consider every **non-empty prefix** of its normalized text.

A query matches that surface when its normalized typed text can be changed into at least one such prefix using no more than `max_edits` single-character operations, where one operation is exactly one of:

- insert one character;
- delete one character;
- substitute one character.

For a particular surface, choose its best qualifying prefix using these rules in order:

1. fewer edits;
2. fewer remaining completion characters after that prefix;
3. lexicographically smaller normalized surface text.

The `completion_chars` value is the number of normalized code points after the chosen prefix.

A canonical term can qualify through its canonical text, any alias, or several of them. Return that term only once. Choose the term's winning surface using these rules in order:

1. fewer edits;
2. fewer `completion_chars`;
3. canonical surface before alias surface;
4. lexicographically smaller normalized surface text;
5. lexicographically smaller alias ID when two aliases normalize identically.

## Result ranking

Rank distinct qualifying active terms using these rules in order:

1. fewer edits;
2. higher `popularity`;
3. fewer `completion_chars`;
4. lexicographically smaller normalized canonical text;
5. lexicographically smaller `term_id`.

Return at most `limit` terms.

A resolved line has this shape:

```json
{
  "request_id": "q-001",
  "status": "resolved",
  "suggestions": [
    {
      "term_id": "term-17",
      "text": "wireless earbuds",
      "matched_surface": "bluetooth earbuds",
      "edits": 1,
      "completion_chars": 10
    }
  ]
}
```

`text` is always the canonical display text from `terms.csv`. `matched_surface` is the original display text of the winning canonical or alias surface.

If nothing qualifies, emit a resolved result with an empty `suggestions` array.

Malformed query objects, missing fields, invalid normalized text, `max_edits` outside `0..2`, non-integer `limit`, or `limit` outside `1..10` produce:

```json
{"request_id":"q-bad","status":"invalid","reason":"invalid_query"}
```

An invalid query must not stop later queries. If `request_id` itself is missing or empty, use `null` in the output.

## Acceptance criteria

- Emit exactly one result per query, preserving input order.
- Search only terms in the query's exact locale. Locale comparison is case-sensitive.
- Inactive terms are never returned, even when an alias matches perfectly.
- A query can qualify against either canonical text or an alias, but one canonical term appears at most once.
- Exact duplicates of one alias row behave as one logical alias; conflicting reuse of an `alias_id` fails snapshot validation.
- Alias references to unknown terms fail snapshot validation.
- Duplicate `term_id` values fail snapshot validation, even when the rows are identical.
- `popularity` must be a non-negative integer; `active` must be exactly `true` or `false`.
- Canonical and alias texts must normalize to a non-empty value.
- Matching uses Unicode code points after the supplied normalization rules.
- A prefix boundary is part of the contract: extra characters after the chosen prefix contribute to `completion_chars` but do not themselves require edits.
- Insertions, deletions, and substitutions near the end of the typed text must behave the same as mistakes in the middle.
- Different searchable surfaces may normalize to the same text; results must still be deterministic.
- Results must not depend on CSV row order, alias row order, object/map iteration order, or process hash behavior.
- A query with `max_edits = 0` is exact-prefix matching after normalization.
- Diagnostic logging belongs on stderr; stdout must remain JSONL.

## Production constraints

The checked-in fixtures are intentionally tiny. Design for approximately:

- 12 million canonical terms;
- 25 million aliases;
- 60 locales, with strongly skewed locale sizes;
- normalized surfaces up to 80 code points;
- normalized query text up to 48 code points;
- `max_edits <= 2` and `limit <= 10`;
- 50,000 suggestion requests/second per process at peak;
- very hot one- and two-character prefixes;
- many terms sharing identical normalized surfaces;
- immutable snapshots replaced atomically outside this process;
- memory budget around 1.25 GB;
- target p95 below 4 ms after startup for typical queries.

A production-credible solution must not scan all terms or aliases for every request, compute full query-to-surface comparisons across an entire locale, or sort every qualifying term when only the first few results are needed.

You may preprocess the immutable snapshot once. Be ready to explain how work grows with query length, allowed edits, branching in the searchable vocabulary, hot prefixes, and `limit`.

The candidate owns the solution strategy. A deterministic solution is natural because the ranking contract is exact, but heuristic, generated, AI-assisted, or hybrid approaches are defensible only if you can state which guarantees they preserve and which they give up. No external API is required.

## Expected deliverable

Implement the suggestion capability behind `Suggester.resolve(query)` in `src/suggester.js` and change supporting code as needed.

Add focused tests for the correctness risks you consider most important. Be prepared to explain:

- what reusable state you build at snapshot load time;
- how a query avoids touching the full locale vocabulary;
- how you handle typing mistakes without producing duplicate canonical terms;
- how exact ranking and deterministic ties are preserved;
- how you avoid unnecessary sorting/work when `limit` is small;
- startup time, memory cost, and per-query complexity;
- what happens on very short hot prefixes and on `max_edits = 2`;
- which malformed-data and boundary cases you verified;
- whether an AI/model component belongs in the critical lookup path.

## Run / verify

Node.js 20+ is sufficient; there are no third-party runtime dependencies.

Baseline checks before changing anything:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

Fixture validation is equivalent to:

```bash
node suggest.js validate \
  --terms fixtures/terms.csv \
  --aliases fixtures/aliases.csv \
  --queries fixtures/queries.jsonl
```

After implementing the resolver:

```bash
node suggest.js resolve \
  --terms fixtures/terms.csv \
  --aliases fixtures/aliases.csv \
  --queries fixtures/queries.jsonl
```

## Scope / out of scope

In scope: immutable snapshot loading, exact normalization, typo-tolerant prefix suggestion semantics, alias reconciliation, deterministic top results, validation, focused tests, and production-scale reasoning.

Out of scope: personalization, click feedback, online learning, semantic/vector search, spell-correction dictionaries outside the supplied surfaces, live snapshot mutation, persistence, distributed caching, HTTP serving, authentication, and UI work.

## 60-minute AI-assisted interview instruction

You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect the repository and fixtures yourself before delegating implementation. Write down the matching and ranking rules in your own words, implement incrementally, verify adversarial boundaries, and be ready to defend both correctness and scale. A one-shot solution that happens to match the small fixture is not sufficient.
