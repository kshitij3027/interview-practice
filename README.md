# SignalWatch — Incident Phrase Triage

## Customer / business context

A managed-service provider receives short incident descriptions from customer support channels. Its incident review team maintains tenant-specific **known issue signatures** (short sequences of words) with priorities. The upstream CSV export contains corrections and retractions, and incoming descriptions are messy: punctuation, capitalization, repeated phrases and overlapping signatures. Analysts need a repeatable, fast answer to **which currently valid signatures appear in each description**. An implementation that loops over every signature for every message already times out in a large customer environment.

Build **one incident-signature screening capability**. You own the strategy, including deterministic, heuristic, LLM-assisted or hybrid approaches. Whatever approach you choose must meet the observable exactness and production constraints. No model credentials or external API are necessary.

## Supplied data and working starter

- `fixtures/tenants.csv`: `tenant_id,display_name`. Tenants are independent; the name is just UI metadata.
- `fixtures/signatures.csv`: `signature_id,revision,op,tenant_id,phrase,priority`. Rows can arrive in any order. Each signature ID belongs permanently to a single tenant. `upsert` revisions supply a phrase and priority; `retract` revisions leave both fields blank. The highest numeric revision per ID is authoritative, even when an older row appears later in the file.
- `fixtures/events.jsonl`: one independent screening request per **physical line**. It deliberately contains both valid and invalid examples. Repeated `event_id` values are separate requests.
- `signalwatch/`: functioning catalog validation, request parsing, and text normalization, plus an unfinished screening method in `engine.py`.
- `signalwatch.py`, `tests/`, `scripts/`: working CLI and green starter checks, which do **not** cover the entire requested capability.

All CSV headers must contain exactly the documented columns (in any order). Identifiers use case-sensitive ASCII letters, digits, `_` or `-`, length 1–48; event IDs allow 1–128. `display_name` is nonempty printable ASCII, length at most 80. Revisions are canonical decimal integers 1..2,000,000,000. Priorities are canonical decimal integers 1..9. `phrase` is **1 to 8 lowercase ASCII alphanumeric tokens**, each 1..24 characters long, separated by exactly one space. No leading or trailing spaces.

Identical replays of the same `(signature_id, revision)` are harmless. Two different contents at the same revision invalidate the **whole catalog**, as do cross-tenant reuse of an ID, undeclared tenants, malformed CSV, or invalid even-superseded records. A retraction does not delete past records; it makes the latest state inactive. Two different signature IDs may have identical phrases and must be treated independently. Catalog errors must cause nonzero exit, a meaningful stderr message, and **no partial screening output**.

## Primary request

Implement `SignatureScreen.evaluate(event)` in `signalwatch/engine.py` and any justified initialization/preprocessing. A valid JSONL input line looks like:

```json
{"event_id":"evt-24","tenant_id":"NORTH","text":"The CARD-payment declined again; card payment declined!","limit":3}
```

`event_id` and `tenant_id` must be syntactically valid IDs. `text` must be a JSON string of **0..20,000 printable ASCII characters** (`0x20..0x7E`). `limit` must be an actual JSON integer from 0 to 10, not a float, string, or boolean. Extra keys can be ignored.

Tokenize the description by taking each **maximal contiguous run of ASCII letters `A-Z`/`a-z` or digits `0-9`** as one token, folding ASCII uppercase to lowercase. Every other allowed character is a separator; successive separators create no empty tokens. Token positions are zero-based. A signature matches only if all of its tokens occur **consecutively**, in order, as complete tokens. For a matched signature, `first_token` is the lowest starting token index at which that signature occurs. Repeated occurrences of one signature still count **once**.

For a valid known-tenant event, return exactly:

```json
{"event_id":"evt-24","status":"ok","total":4,"matches":[{"signature_id":"sig-x","priority":9,"first_token":1}]}
```

The values above illustrate shape only, **not** expected fixture answers. `total` is the number of **distinct active signature IDs** belonging to the specified tenant that appear at least once, **before** applying `limit`. Sort all distinct matches by **priority descending**, then **first_token ascending**, then **signature_id ascending in case-sensitive lexicographic order**. Return at most `limit` entries in `matches`, even when limit is zero. It is possible for two IDs with identical phrases to appear in the output separately.

Invalid JSON, wrong field types, missing fields, invalid IDs, out-of-range limits, or invalid text yield `{"event_id":null,"status":"invalid","reason":"invalid_event"}`, retaining an event ID instead of null only when its field is a syntactically valid event ID. A structurally valid request for an undeclared tenant yields reason `unknown_tenant` and preserves event ID. Each bad line is isolated; later lines still produce outputs. Every input physical line, **including empty lines**, produces one compact JSON response line in the original order. No diagnostic logs on stdout.

## Observable acceptance criteria

1. Match complete normalized tokens, never substrings: `pay` is not the token `payment`; `code404` is not `code 404`.
2. Permit matches through any punctuation or repeated separators, while preserving consecutive-token semantics; `A-C` gives tokens `a`,`c`, not `ac`.
3. Detect overlapping signatures and nested phrases independently, including two signatures that share the exact phrase.
4. Report only the earliest token occurrence for each distinct active signature ID, even if it repeats later.
5. Apply the correct tenant's highest revision regardless of CSV order; honor retractions, duplicate revisions, and live replacements.
6. Sort by the specified three-part order and compute `total` independent of `limit`. Tie comparisons are case-sensitive; `sig-10` comes before `sig-2`.
7. Handle empty descriptions, messages without tokens, repeated event IDs, non-ASCII descriptions, zero limit, unknown tenants, malformed JSON and empty JSONL lines as specified.
8. Reject bad catalogs atomically; one malformed request cannot corrupt subsequent outputs. Produce deterministic results independent of catalog row order and harmless retry records.

## Production constraints

The compact fixture represents up to **900,000 active signatures**, **3 million revision rows**, **100 tenants**, and **4 million screened descriptions per day**. A description may contain **10,000 tokens**, and up to ten signatures are returned. Most queries target a handful of hot tenants, phrases frequently share long beginnings, and some descriptions repeat the same common phrase thousands of times. Target **p95 under 60 ms after snapshot load** for typical descriptions on a warmed process, using **under 1.5 GB** process memory; these are design targets, not locally enforced benchmarks. A per-event full signature scan or substring search for every phrase is not production-ready. Discuss index/build cost, query time in terms of text length and matches, memory, and how to verify correctness with a small independent oracle.

## Deliverable, run commands, and scope

Python 3.11+ standard library only. Keep the `SignatureScreen.evaluate(event)` interface and JSONL command contract. You may reorganize code and add focused tests. Do not build a UI, persistent database, machine-learning training pipeline, live customer connector, streaming subscription, or administrative signature editor. Do not modify fixture values to make tests pass.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 signalwatch.py check --tenants fixtures/tenants.csv --signatures fixtures/signatures.csv
python3 signalwatch.py scan --tenants fixtures/tenants.csv --signatures fixtures/signatures.csv --events fixtures/events.jsonl
```

`check` works in the starter. `scan` can process malformed/unknown-tenant requests; its valid-request screening method deliberately remains unimplemented until you solve the task.

**60-MINUTE AI-ASSISTED INTERVIEW:** Use Claude Code, Codex, ChatGPT or similar tools as you would on a real customer issue. First inspect the supplied data, contracts, and tests; decide and explain a strategy; implement incrementally; run checks and test nontrivial cases; and be ready to defend correctness, limits, complexity, and tradeoffs. Your interviewer is interested in judgment and verification, not memorized syntax. Stop after 60 minutes and explain what is complete and what remains.
