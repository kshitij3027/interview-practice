# ScanLedger — HARD 60-minute AI-assisted customer interview

## Customer context
A parcel carrier has a planned ordered list of checkpoints for each delivery route. Barcode scan tapes from depots, trucks, and handheld scanners may omit checkpoints, contain extra scans, or name the wrong location. Repeated facilities are legitimate. The customer needs an exact, explainable correction audit, rather than a partial guess, for tens of thousands of tapes.

## Supplied data
- `fixtures/routes.csv` contains `route_id,carrier,sequence`. The sequence is nonempty and pipe-separated. `carrier` is metadata. Replayed identical rows are harmless; conflicting definitions of one route ID invalidate the catalog.
- `fixtures/observations.jsonl` contains independent queries with nonempty string `request_id`, nonempty string `route_id`, array `scans` (possibly empty), and integer `max_repairs` in [0,16] (boolean is invalid).
- Checkpoint codes are case-sensitive, uppercase ASCII, 2–16 characters, and start with a letter; remaining characters may include digits and underscores. Unknown scanned codes are legal.

## Feature request
Implement `ScanAuditor.reconcile(route, scans, max_repairs)` in `tracekit/auditor.py`. Return a list of repairs in alignment order, or `None` if the **globally minimum** number of repairs exceeds the budget. A full reconciliation consumes the entire observed tape and planned route without reordering positions. A matching pair of codes consumes both positions at no cost. Otherwise, each of the following costs one repair: `missing` inserts the next planned checkpoint, `unexpected` removes the next observed scan, and `incorrect` replaces a differing observed code with the next planned code. No substitution is legal for equal codes.

Choose the winning complete alignment by: (1) fewest repairs; (2) among ties, fewest `incorrect` steps; (3) among ties, lexicographically smallest **full step-type sequence, including matches**, using `match < missing < unexpected < incorrect`. Offsets are zero-based positions in the original unmodified tapes, not post-edit positions. Repair objects include `type`, `observed_offset`, `expected_offset`, and `observed_code` or `expected_code` as appropriate. See `CONTRACT.md` for exact examples and schemas.

## Acceptance criteria
Handle repeated checkpoints, swaps, duplicate route deliveries, empty scans, exact matches, trailing insertions/deletions, unknown codes, global tie-breaking, and the inclusive repair budget (including zero). Do not emit partial plans. An invalid catalog fails with nonzero exit and a stderr diagnostic. Invalid queries, unknown route IDs, and malformed JSON do not stop later lines; preserve a nonempty string request ID when available. Output one JSON object per request line, in original order, with no stdout diagnostics. Results must be independent of route file ordering and hash iteration.

## Production constraints
A snapshot can hold **3 million planned checkpoints**, with one route or scan tape up to **200,000 tokens** and **50,000 audits**. `max_repairs <= 16`. Target **256 MB extra working memory** and **250 ms typical p95 for 10,000 tokens with budget 8** after loading. Treat these as targets to justify and benchmark. A full pairwise-comparison table is not acceptable; neither truncation nor approximate answers satisfies this contract.

## Scope / deliverable
In scope: exact reconciliation, deterministic output, error handling, tests, complexity/performance reasoning, code walkthrough. Out of scope: physical route optimization, GPS, editing original scans, a UI, databases, training, or changing repair costs. Whether any AI or heuristic belongs in the approach is your decision, but accuracy requirements remain exact.

## Setup and verification
Python 3.11+, no external packages or credentials.
```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 scan_audit.py validate --routes fixtures/routes.csv
```
After implementation:
```bash
python3 scan_audit.py reconcile --routes fixtures/routes.csv --observations fixtures/observations.jsonl
```
Starter checks cover the loader/CLI baseline, not the missing audit implementation.

## 60-minute AI-assisted instruction
You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or other AI tools. Inspect the fixtures, choose a strategy, implement it, add adversarial tests, and explain correctness, tie-handling, scaling to long tapes, and where one-shot AI code might fail. Evaluation includes your technical walkthrough.
