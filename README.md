# ClaimSignal — HARD 60-Minute AI-Assisted Systems Interview

## Customer and business context

An insurance claims platform receives millions of short adjuster notes from email, phone transcription, and live chat. Claims operations maintains a catalog of exact evidence phrases that indicate issues requiring specialist follow-up. The catalog deliberately contains overlapping phrases and competing issue codes: a note may contain several possible annotations of the same text, but the downstream review system must not double-count overlapping evidence.

Analysts currently scan each note against every phrase and keep locally attractive hits. This is slow against the production catalog and can produce a worse collection of evidence than another set of non-overlapping annotations. Build the production-facing resolver for **one immutable catalog snapshot and a stream of independent claims notes**. You choose the technical approach.

## Supplied data

`fixtures/rules.csv` is a catalog with `rule_id`, `issue_code`, `phrase`, `weight`, `channels`, and `active`. The same `rule_id` may be delivered more than once **only when the entire row is identical**; such retries count once. Conflicting reuse of an ID is a fatal catalog error. Different rule IDs may share a phrase or issue code. A rule marked `false` is ineligible. `channels` is either `*` (all channels) or a pipe-delimited nonempty subset of `email`, `phone`, `chat`. Weight is a positive integer, 1–100. Phrases contain printable ASCII letters, digits, spaces, or hyphens, 1–120 characters, without leading/trailing or repeated spaces. Phrase text is not necessarily unique.

`fixtures/cases.jsonl` contains independent requests. A request has `case_id` (nonempty string), `channel` (`email`, `phone`, or `chat`), `text` (ASCII string), and `max_findings` (integer 1–8). An invalid JSON line or invalid request must produce a query-level invalid result **without stopping later lines**. Request IDs may recur: every line is processed independently. Text may contain ASCII punctuation, tabs, and newlines; offsets count characters from zero. An empty note is valid. The input file may be arbitrarily ordered.

## Primary feature request

For each case, identify eligible occurrences of catalog phrases in its note, then return the **best set of at most `max_findings` non-overlapping findings**. Exact output is required, not a greedy approximation on ordinary valid requests.

A phrase occurrence matches ignoring **ASCII case only** (`A`–`Z` compare as `a`–`z`). Do not normalize spaces, punctuation, accents, or hyphens. An occurrence `[start, end)` is valid only if the character immediately before `start`, when present, and the character at `end`, when present, are **not ASCII letters or digits**. For example, `leak` does not match inside `leaking`, but may match after a hyphen. A phrase can occur repeatedly, including at overlapping locations. Rules only apply to their allowed channel. Two distinct rules matching exactly the same characters are competing findings, not a deduplication opportunity.

Each candidate finding has `score = rule.weight * (end - start)` and `characters = end - start` (spaces and hyphens inside a phrase count). A selected set cannot reuse any character position: two selected `[start,end)` intervals must be disjoint; adjacent intervals are permitted.

Choose the unique winning set by comparing **complete sets**, in order:

1. Greatest total `score`.
2. Greatest total `characters` covered.
3. Fewest selected findings.
4. Lexicographically smallest sequence of `(start, end, rule_id)` tuples after sorting that sequence by `(start, end, rule_id)`.

The empty set is valid and has zero totals. Never select more than `max_findings`. This global ranking is part of the contract, including when one longer match competes with several shorter matches.

## Observable output and acceptance criteria

The `resolve` command emits **one JSON object per input line**, in original order, with no diagnostics on stdout. For a valid case:

```json
{"case_id":"example","status":"resolved","total_score":60,"covered_characters":10,"findings":[{"start":0,"end":10,"rule_id":"R01","issue_code":"WATER","score":60,"text":"water leak"}]}
```

The object above illustrates the **response shape only**, not a guaranteed fixture result. `findings` must be sorted by `(start,end,rule_id)` and their `text` must be the exact original slice (preserve source capitalization). Invalid requests emit `{"case_id": <valid ID or null>, "status":"invalid", "reason":"invalid_request"}`. Fatal catalog errors cause a nonzero process exit and a useful stderr message.

Your implementation must handle all of the following correctly:

- Identical catalog replay rows versus conflicting reuse of one rule ID; independent rules can share a phrase.
- Matches competing over partially or completely overlapping spans, and non-overlapping matches where a locally best choice sacrifices a better total result.
- Exact whole-token boundaries with hyphens, punctuation, digits, start/end of text, and case-insensitive comparison.
- Multiple occurrences of one phrase, including overlapping occurrences; a finding may use each occurrence independently.
- Channel-specific eligibility, inactive rules, and phrases which do not appear in a note.
- At-most-`k` constraints and every tie level, regardless of catalog row order or dictionary iteration order.
- Empty text, malformed JSON, wrong numeric types (including booleans), bad channel, and a later valid line after an invalid line.
- No cross-request contamination, even when case IDs repeat.

## Production constraints and expected deliverable

The snapshot may contain **150,000 rules** and **3 million notes**, with typical notes around 3,000 characters, sometimes 100,000 characters; `max_findings` is at most 8. Shared catalog preprocessing is allowed, but design for about **1 GB RAM** and an aspirational **p95 below 100 ms for ordinary 3,000-character notes after preprocessing**. An approach that loops through every phrase for every note, enumerates all possible finding combinations, or copies the catalog per request is not credible at scale. Describe time/space cost both for preparation and for a note with `n` characters and `h` candidate occurrences, including high-overlap adversarial notes. Partial credit is available for a sound incrementally built implementation with demonstrated correctness and a defended scaling path.

Implement `ClaimResolver.resolve_case(...)` in `claimsignal/service.py` and any supporting files/tests you need. The starter supplies catalog loading, validation, CLI commands, and baseline tests; the requested resolver is deliberately absent.

## Scope and out of scope

In scope: exact phrase evidence resolution, consistent output, input validation, clear errors, and appropriate runtime/memory tradeoffs. Out of scope: OCR, embeddings, external LLM APIs, fuzzy matches, persistent databases, web UI, changing the catalog during this run, or editing fixtures to make tests pass.

## Setup, run and verify

Python **3.11+**, standard library only:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

After implementing the feature:

```bash
python3 claimsignal.py resolve --rules fixtures/rules.csv --cases fixtures/cases.jsonl
```

The starter `validate` command confirms snapshot and request syntax; successful validation does **not** mean the new feature is implemented. The baseline unit tests intentionally do not cover full feature acceptance.

## 60-minute AI-assisted interview

You have exactly **60 minutes**. Claude Code, Codex, ChatGPT, and other AI assistants are permitted. First inspect the supplied data and starter code; then determine your approach, implement incrementally, test observable behavior, and explain correctness, production complexity, failure modes, and tradeoffs. Expect to defend the solution and identify where an AI-generated implementation might be subtly wrong.
