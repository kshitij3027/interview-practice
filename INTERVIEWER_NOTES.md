# POST-PRACTICE ONLY — SignalGate interviewer notes

**Evaluator-only material.** Do not expose these notes or their tests to the candidate before the 60-minute attempt. The candidate branch was created from a clean initial commit and must never inherit this branch.

## Intended underlying problem structure

This is **exact multi-pattern substring matching over a byte stream**, complicated by tenant/region eligibility, time-window filtering, duplicate IDs and patterns, chunk boundaries, earliest occurrences, deterministic top-K and an all-matching-ID count. It is not semantic keyword classification. A single substring search for each signature costs roughly O(P × B) per body and cannot meet 200k patterns × millions of requests/day. The hidden structure is a **trie with failure links (Aho–Corasick)**, or an equivalent byte-oriented multi-pattern index with a rigorous complexity argument.

One reasonable construction:

1. Validate and deduplicate the catalog using the supplied loader. Filter disabled signatures from the immutable scan index. Group signature records by **identical raw pattern bytes**; one search terminal may correspond to multiple different signature IDs.
2. Build a byte-oriented trie over unique patterns and failure links via breadth-first search. Keep each node's own terminal pattern identifiers and an output/suffix link to the next failure ancestor with terminals. Avoid copying all suffix-output arrays into every state when highly nested patterns would amplify memory.
3. Scan the base64-decoded chunks **in order**, retaining search state across chunk boundaries. Empty chunks are transparent. Maintain one global byte index and follow transitions/failure links for each byte. For a terminal of pattern length `L` at zero-based ending byte `i`, the start is `i - L + 1`.
4. Apply global-or-exact-region, `enabled`, and half-open `valid_from_ms <= seen_at_ms < valid_until_ms` gates for **each ID**, even when many IDs share a terminal pattern. Record the first start for each eligible matching ID in a per-request map, never replacing it with a later match.
5. After scanning, `total_matching_signatures = size(map)`. Order all distinct matches by `(-priority, earliest_start, signature_id)` using case-sensitive strings, return at most `limit`. A bounded heap can choose top K while still maintaining the total count, but stopping the scan at K is incorrect.

A well-implemented Aho–Corasick matcher has construction cost around O(sum of pattern lengths + transition work), and per-query cost O(body bytes + relevant emitted terminal occurrences), plus O(M log M) sorting of M distinct matched IDs (or O(M log K) selection). Worst-case output reporting can be expensive when a hot short signature matches at every byte, or many suffix patterns terminate at each state. Candidate should explicitly state this and discuss skip-already-seen optimizations, prefiltering scopes/times, or compact output indexing. Binary alphabet size is 256, but a 256-element transition table at every node may exceed memory; sparse maps, packed arrays, or compiled representations trade speed for space. Four million total bytes can create millions of states, and a naive Python object-per-node design can exceed 1.5 GB: do not accept hand-wavy Python memory claims.

## Why naive/one-shot approaches fail

- A loop of `payload.find(pattern)` per signature is straightforward and may pass tiny fixtures, but its O(P × B) query work is unacceptable.
- Searching each **chunk separately** loses matches spanning chunks, including those separated by zero-length chunks.
- Decoding base64 to UTF-8, normalizing text, or using case-insensitive search corrupts semantics: these are arbitrary bytes, including `0x00` and `0xff`.
- Returning the first physical match or first K discovered matches breaks priority ranking. Returning only K items as the total also breaks the required count.
- Using a `pattern -> single signature` dictionary loses distinct IDs sharing the same bytes.
- Caching by `request_id` is incorrect because request IDs can repeat for different bodies/times/regions.
- Applying the time window with `<= valid_until_ms` incorrectly includes a signature at expiration.
- Grafting an LLM onto byte matching introduces false positives/negatives, latency and cost without helping the exact contract. A candidate may justify AI for development/testing, but model output is not an exact substring oracle.

## Expected facts the candidate should discover

The fixtures contain 3 declared regions, 16 distinct signature IDs (17 rows including one replay), overlapping pattern bytes with distinct IDs, global and region-specific signatures, disabled entries, boundaries at `800` and `1000` ms, binary `ff00` and `0061` patterns, a long `abcde` pattern, empty chunks, a repeat of a query ID, invalid JSON and base64, and an unknown region. Catalog row order is irrelevant.

Representative fixture expectations for a completed implementation:

- `scan-east-1` at 150 ms has payload `abcde` split across four chunks, including an empty chunk. There are **8 distinct eligible matching IDs**. The first four ordered IDs are `SIG-A11`, `SIG-A16`, `SIG-A15`, `SIG-A14` (the longer `SIG-A14` sorts before `SIG-A2` at their identical priority and offset because uppercase/case-sensitive lexicographic ordering is literal). Top-K cardinality is 4, total is 8.
- `scan-raw` at 250 ms has raw bytes `00 61 62 63 ff 00`. `SIG-A4` matches at start 0 (priority 100), `SIG-A12` at start 4 (priority 90), `SIG-A15` at start 1 (priority 40); the payload has **8 distinct** eligible IDs.
- `scan-boundary` at exactly 1000 ms matches only the newly effective `SIG-A9`, not the global signatures whose end is 1000.
- `scan-emea` at exactly 800 ms must exclude `SIG-A5`. The highest-priority matching IDs are `SIG-A16` then `SIG-A13`; the total is 3.
- `scan-no-match` at 9999 ms must report zero even though its payload contains `abc`: relevant rules have expired.
- `scan-east-1` reoccurs at 500 ms with a different payload and a limit of 1; it must be evaluated independently, not deduplicated by request ID.

## Hidden checks / adversarial cases

1. Generate a single pattern split into 64 one-byte chunks with empty chunks inserted; verify offsets and absence of artificial delimiters.
2. Repeated `aa`, `aaa`, `aaaa` over `aaaaaa`: overlapping occurrences, earliest start 0 for each ID, one distinct count per ID, and suffix-heavy output behavior.
3. Two IDs with identical raw bytes but different scopes/priorities; both count in the applicable region; an identical replay of one ID does **not** count again.
4. Global vs. regional signatures, disabled entries, and exact effective time boundaries at start and end (including 0 and 10^12).
5. Equal priority and equal starts, choose case-sensitive ID sort; equal priority at different offsets, choose earlier offset regardless of ID; a later high-priority match outranks an earlier low-priority match.
6. `limit=1` with 1000 distinct matching IDs: `matches` is length 1 but `total_matching_signatures` is 1000.
7. NUL/high-bit bytes and patterns that start/end inside different chunks; verify raw byte offsets instead of UTF-8 character or base64 offsets.
8. Invalid base64 encodings (missing padding, illegal whitespace, noncanonical pad bits), `true` for timestamp/limit, non-object JSON, negative numbers, 41-character region, oversized chunk/payload, malformed catalog, and per-query continuation.
9. Shuffle signature rows, region rows, chunk boundaries, query order, and repeat request IDs; outputs for equivalent requests must remain identical except their original stream positions.
10. Benchmark many prefixes/suffixes, repeated short patterns, 200k IDs and dense matches. Discuss measured build/query/memory statistics rather than insisting on an unverified latency promise.

A useful independent small-input **oracle** uses Python `bytes.find` on `b''.join(chunks)` **once per eligible signature**. That is too slow for production but valid for differential tests on a compact randomly generated catalog. Compare all result fields and shuffled/chunked variants. The evaluator-only tests can be run with `python3 -m unittest discover -s evaluator -v` after implementation, not on the untouched starter.

## 60-minute interview plan and walkthrough probes

- **0–8 min:** Explore fixture and schema; identify that chunk concatenation and distinct eligible IDs determine semantics, and that scanning every signature is unacceptable at production scale.
- **8–18 min:** Sketch/index design and exact result ordering. Ask about time/memory constraints and acknowledge runtime-dependent limits.
- **18–40 min:** Implement core index/search across chunks and region/time filters. Prioritize output correctness and robust interfaces.
- **40–52 min:** Add tests for overlapping patterns, shared bytes, chunk crossings, window boundaries, tie ordering, binary data and top-K count.
- **52–60 min:** Run tests, inspect diffs, explain build vs. query complexity, suffix-output fan-out, memory tradeoffs and any gaps.

Ask: “Why does your choice avoid O(number of signatures) work for every ordinary body?” “Can a match begin in one chunk and end in another without concatenating a megabyte buffer?” “How do you handle distinct IDs with identical patterns?” “How do you know the earliest start offset?” “What if 100k IDs all match and the customer requests limit=2?” “Does the strategy satisfy 1.5 GB in CPython, or is this an estimate that needs benchmarking?” “When could a heuristic or model safely participate without compromising exactness?”

Alternative defensible designs include a compiled regex multi-pattern engine **if** exact binary escaping, offsets, duplicates, match overlaps, output completeness, and scalability are verified; partitioned deterministic indexes by scope or time; or a high-performance native library with clear API and correctness tests. Award design points based on evidence, not nomenclature.
