# MirrorTrace — HARD 60-minute AI-assisted customer interview

## Customer / business context
A large resale marketplace is struggling with sellers recycling product photographs from previously removed listings. Its moderation team stores compact, 128-bit image fingerprints generated upstream by a separate imaging service. A low-level difference in a few fingerprint bits often indicates a visually reused image, although the fingerprints are not a substitute for a human determination of abuse.

A prototype compares every candidate fingerprint to every existing listing, which works for a few hundred records and times out at production volume. Build the **exact candidate-retrieval component** for a fixed, read-only marketplace snapshot. The component is used to queue images for manual review, not to automatically penalize sellers.

You decide the implementation approach and how to justify it to the customer. You may use coding assistants. No external API, credentials, or machine-learning model is required.

## Supplied data
- `fixtures/listings.csv`: `listing_id,market,seller_id,first_seen_ms,last_seen_ms,fingerprint_hex,risk_score`. Each listing has exactly one 128-bit fingerprint rendered as **32 hexadecimal characters**. `last_seen_ms` is either an integer or `*` (no known end). Time ranges are half-open: `[first_seen_ms,last_seen_ms)`. `risk_score` is an integer 0–100 and is only a ranking signal; it is not a probability.
- `fixtures/requests.jsonl`: one independent review request per line. A valid request contains `request_id`, `market`, `seller_id`, `as_of_ms`, `fingerprint_hex`, `max_bit_errors` (0–3), `limit` (1–20), and `min_risk_score` (0–100). Unknown markets are valid and simply produce no matches. Repeated request IDs are independent requests.
- The complete input validation/parsing and output harness are provided in `data_io.py` and `main.py`. The retrieval component in `gallery.py` is **not implemented**.

A fingerprint's difference is the **number of bit positions that disagree** between two 128-bit values (not the number of differing hexadecimal characters). Leading zeroes are significant to the 128-bit representation, but do not make two numerically equal fingerprints different. Uppercase and lowercase hex letters are equivalent.

The snapshot loader collapses identical replay rows with the same `listing_id`. Conflicting reuse of a listing ID, invalid time bounds, or malformed fingerprints makes the entire snapshot invalid. Each malformed JSON request must instead return a per-request error, without stopping the following requests. All timestamps are nonnegative integer milliseconds; booleans are not integers for validation purposes. IDs are case-sensitive.

## Primary customer request
For each valid request, find all listings that satisfy **every** filter: same `market`; `seller_id` different from the request's seller; `first_seen_ms <= as_of_ms < last_seen_ms` (or no end); `risk_score >= min_risk_score`; and fingerprint difference at most `max_bit_errors`.

Return at most `limit` matches, ranked in this **exact** order:
1. fewer disagreeing fingerprint bits;
2. higher `risk_score`;
3. more recent `first_seen_ms`;
4. lexicographically smaller, case-sensitive `listing_id`.

Do not return the same listing twice, even if duplicate source rows exist. If there are no eligible matches, return an empty list. Ties must be deterministic regardless of input row ordering or query order.

Valid request response shape (JSONL, one line for each input request):

```json
{"request_id":"r-1","status":"resolved","matches":[{"listing_id":"L-A","bit_errors":1,"risk_score":84}]}
```

Malformed requests instead return `{"request_id":null,"status":"invalid_request","error":"..."}` (use a valid request ID when recoverable). The supplied harness handles this behavior. It currently returns `status = "not_implemented"` for valid requests until you implement `Gallery.find`.

## Production constraints
The checked-in fixtures are intentionally small. The customer's planned snapshot contains approximately **6 million listings**, across **50 markets**, with up to **3 million independent lookup requests per day**. Fingerprints are highly skewed: popular stock photos may appear in **hundreds of thousands** of listing rows, often from different sellers. Queries have different time points, seller exclusions, risk thresholds, and limits. Allow approximately **2.5 GB working memory** and target **sub-30 ms p95** per typical request after one-time indexing. An all-listings scan for each request is not a credible production design.

The correctness requirement is exact: an approximate method is only acceptable if it can prove it never excludes any eligible record. Returning plausible-but-not-best matches is not sufficient. Discuss when performance may degrade (including skewed fingerprints), what should be measured, and how you would improve the design if the customer's mix changes.

## Deliverable and observable acceptance criteria
Implement `Gallery.find(query)` in `gallery.py`, changing other files only as needed for a credible approach. It must return a list of `(Listing, bit_errors)` pairs ranked correctly, and each returned listing must satisfy all conditions above. The provided harness serializes those pairs to JSONL. Be ready to walk through the data structures, complexity, edge cases, any AI-generated code you kept, and why your approach respects exactness.

A strong solution addresses varying distance thresholds, fingerprint collisions and duplicate listings, high-volume lookups, cross-market isolation, timestamp boundaries, the requester's own seller, risk filtering, sorting ties, and cases with fewer than `limit` results. The returned order must not depend on input order.

## Scope
In scope: immutable snapshot preparation, exact retrieval and ranking, validation of results, explanation of scale/performance tradeoffs. Out of scope: feature extraction from actual photos, live updates, user authentication, moderation decisions, databases, hosted embeddings, model training, UI work, distributed sharding.

## Setup / verification
Requires Python **3.11+**, standard library only. From the repository root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 main.py --fixtures fixtures
```

`--validate-only` checks the dataset without running the missing retrieval logic. The baseline tests deliberately test the parsing and harness, **not** the intended matching algorithm. Write your own focused correctness and scaling tests.

## 60-minute interview instruction
You have **60 minutes** and may use Claude Code, Codex, ChatGPT, or other tools exactly as you would on the job. Inspect the supplied fixture and interfaces first. Decide and defend an approach, implement its most important correctness path, verify with deliberately difficult inputs, and explain its expected time/space behavior. You are not expected to build photo classifiers or provision services.
