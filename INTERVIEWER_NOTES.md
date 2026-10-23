# POST-PRACTICE ONLY — MirrorTrace interviewer notes

**Evaluator-only. Read only after the candidate has completed their 60-minute attempt.**

## What the candidate should discover

The customer has already supplied 128-bit fingerprints. The task is an **exact fixed-radius nearest-neighbor retrieval problem in binary fingerprint space**, with customer-specific eligibility filters, top-k ordering, and a highly skewed immutable snapshot. It is not image classification, text similarity, or an LLM prompting challenge. The constraints rule out scanning all six million listings independently for each query, and the exactness requirement rules out ordinary approximate retrieval without a completeness guarantee.

The core difficulty is reducing candidate generation without missing any bit-close item. The remaining challenge is filtering, full ordering, and skew control under strict memory/latency goals.

## Strong exact solution outline

**Simple correctness oracle (small inputs):** parse each 128-bit fingerprint as an integer, compute differing bits using exclusive-or and population count, apply all eligibility filters, and sort matches by (`bit_errors` ascending, `risk_score` descending, `first_seen_ms` descending, `listing_id` ascending). This is useful as a reference test but not as production retrieval.

**Scalable candidate generation:** partition the 128 bits into four disjoint 32-bit blocks. Index distinct fingerprints or records under each key (`market`, `block_number`, `block_value`). Any fingerprint differing in **at most three bits** must agree exactly in **at least one** of the four blocks (pigeonhole principle). Therefore unioning matching postings from those four block keys guarantees no false negatives for any allowed radius 0–3. Deduplicate candidate IDs (or index unique signatures), verify actual full-width differing-bit counts, then apply market/seller/time/risk filters and rank globally. Radius zero can use a direct exact-fingerprint lookup. For radius 1 or 2, more or differently sized blocks can trade index expansion for better posting selectivity, but the four-block index remains complete.

**Skew matters:** if hundreds of thousands of rows share a popular stock-photo fingerprint, naive postings over listing IDs repeatedly touch huge lists even for `limit=1`. Consider grouping by unique (market,fingerprint) and storing candidate rows inside each signature bucket; pre-sort those rows by risk descending, then first_seen descending and listing ID ascending, with seller/time filters applied correctly. Pre-index by market and employ compact integer IDs / packed arrays / compressed postings to avoid Python dict/list overhead on 24 million raw posting entries. Partial early stopping is legal only with a correctness proof that unseen candidates cannot outrank seen candidates. Do not silently cut off hot postings or rely on randomness.

**Alternatives:** enumeration of changed-bit combinations is exact but up to 1 + 128 + 8,128 + 341,376 candidate neighbor signatures for distance 3, so it may be unattractive at millions of queries. A binary metric tree or exact search structure can be discussed; worst-case skew must be addressed. Bitset/vectored approaches also earn credit if completeness and memory are justified. An LLM/hybrid can aid choosing/testing the index, but not make unverified proximity judgments under exact bit semantics.

## Complexity and production discussion

A naive scan is O(N) distance calculations per query, plus result sorting. A four-block inverted index takes O(4U) index references for U distinct signatures (plus per-record metadata), with variable postings size per query; query work is proportional to union size of the four posting lists plus exact checks and chosen top-k maintenance. Worst-case work can still approach O(N) for pathological skew, so never claim unconditional sublinear guarantees. Full sort costs O(M log M) for M eligible candidates; top-k maintenance can use O(M log k) with careful deterministic tie ordering, though filters and signature grouping complicate top-k fast paths. Memory depends heavily on whether postings are stored per record or per unique signature, market sharding, and Python object overhead. Production scale targets are aspirational; only benchmarks establish actual p95/RSS.

## Subtle traps and hidden checks

- Distance counts differing **bits**, not differing hex digits; `0x3` differs from `0x0` in **two** bits. A changed high-order bit (`0x8000...`) is a one-bit difference.
- If the candidate divides fingerprints into blocks and searches only selected blocks or uses a wrong threshold-specific proof, choose differences distributed to expose missed matches.
- `last_seen_ms` is exclusive; `first_seen_ms` inclusive. `*` lasts forever.
- Exclude **every** listing from the requesting `seller_id`, not just one listing ID; requesting seller may have the best matching fingerprint.
- Retain market isolation even when signatures are identical; unknown market returns empty results.
- Risk-score threshold is inclusive. Rank **distance before risk**, despite high-risk nonidentical images.
- Duplicate `listing_id` rows that are identical collapse; conflicting reuse invalidates the snapshot, rather than taking latest.
- Distinct listing IDs may share a fingerprint, even within or across sellers; all eligible entries remain distinct candidates.
- Lexicographic ordering of listing IDs is case-sensitive; a stable result must not depend on load order.
- Query `request_id` can repeat with different payloads and must not memoize to a prior answer by ID.
- Uppercase and lowercase hex are equivalent; validate full 32-character form and nonnegative integer time fields; booleans must not pass as integers.
- Malformed JSON request must return one error and not prevent later valid requests from running; fatal snapshot errors should halt before any lookups.

## Recommended 60-minute pacing

- 0–8 minutes: inspect the fixture, loader, schema, expected ordering, and production targets. Clarify that no images need to be decoded.
- 8–18: implement a brute-force correctness oracle locally, document invariants, and write 3–4 high-value tests.
- 18–43: implement exact index and candidate generation; validate returned list vs oracle on fixture and generated adversarial data.
- 43–53: verify boundary filters, tie-breaking, seller exclusion, duplicate rows, and hot-signature behavior.
- 53–60: walkthrough, asymptotic analysis, limitations, memory accounting, and benchmark plan.

## AI-assisted failure modes

Look for one-shot code that:
1. scans all listings despite 6M-row constraints;
2. computes hex-character distance or string edit distance instead of bit distance;
3. uses embeddings, LSH, or a random subset without proving zero false negatives;
4. picks first k matches before global ranking;
5. drops all but one listing for repeated fingerprints;
6. misses candidates when errors touch separate bit partitions;
7. claims O(1) query time despite unbounded posting collisions;
8. overbuilds an external vector DB before meeting the simple exact contract.

## Post-hour interviewer inspection

Request the candidate's index completeness proof, a small exhaustive reference test, sample results for skewed signatures, exact ordering justification, memory estimate, and discussion of where p95 deteriorates. A clear partial implementation plus correct algorithmic reasoning can outrank an apparently polished solution with incorrect results.
