# SignalGate — HARD 60-minute AI-assisted customer interview

## Customer / business context

A B2B API gateway provider receives binary request bodies in transport chunks. Its abuse-response team maintains a catalog of **exact byte signatures** that indicate known risky payloads. Each signature applies either globally or to one deployment region, has an effective time window, and carries an analyst-defined priority. Operators need to identify the highest-priority distinct signatures seen in each request, not merely the earliest substring encountered. A prototype decodes each body and searches it separately for every signature; it fails at production volume and sometimes misses a signature split across chunks.

Treat this as a real customer escalation. You choose the solution strategy. Deterministic, heuristic, LLM-based or hybrid approaches are permitted if you can defend their ability to meet the exact observable contract. No external SDK, credentials, or network service is required.

## Supplied data

- `fixtures/regions.csv`: `region_id`. Region identifiers are case-sensitive, 1–40 ASCII letters/digits/`_`/`-`. Identical repeated region rows are harmless. Region `*` is reserved and cannot be declared.
- `fixtures/signatures.csv`: `signature_id,region,priority,valid_from_ms,valid_until_ms,pattern_hex,enabled`. A region is `*` (all declared regions) or a declared region. Priority is an integer in `[0,1000]`; larger means more important. The time interval is half-open `[valid_from_ms,valid_until_ms)` in integer milliseconds, with `0 <= valid_from_ms < valid_until_ms <= 10^12`. `pattern_hex` is lowercase, even-length hexadecimal representing **1–64 arbitrary bytes**. `enabled` is exactly `true` or `false`. Signature IDs follow the region ID format. Identical replays of a signature ID with identical data count once; conflicting reuse invalidates the whole catalog. Different IDs may use the **same bytes**, even in the same scope. Duplicate signatures remain distinct findings.
- `fixtures/requests.jsonl`: one independent JSON request per physical line, including malformed examples. Each valid object has `request_id` (1–128 ASCII letters/digits/`_`/`-`), `region`, `seen_at_ms`, `chunks_b64`, and optional `limit` (default 5). `chunks_b64` is a list of **1–128 canonical, padded base64 strings**, each decoding to at most 65,536 bytes; empty chunks are allowed, and total decoded bytes per request may not exceed 1,048,576. The complete payload is the byte-for-byte concatenation of its chunks. `limit` is an integer in `[1,20]` (JSON `true` is not an integer). `seen_at_ms` is a JSON integer in `[0,10^12]`. Extra request fields may be ignored. The base64 representation must round-trip exactly; whitespace, missing padding, or alternate encodings are not accepted.

CSV headers may appear in any order. Canonical CSV integers contain only base-10 digits with no leading zeroes (except `0`) and no signs. Blank required fields, malformed CSV, missing headers, bad region references, invalid intervals, invalid hex, and conflicting signature-ID replays invalidate the **entire** catalog before scanning starts. Per-query errors do not invalidate other queries.

## Primary customer request

Implement `SignalScanner.scan(request)` in `signalgate_pkg/scanner.py` and any supporting code/tests. For each valid request, find **every distinct eligible signature ID** whose byte pattern appears as a contiguous substring of the **concatenated** payload (including occurrences crossing chunk boundaries). A signature is eligible iff it is enabled, its region equals the query region or `*`, and `valid_from_ms <= seen_at_ms < valid_until_ms`. Matches are literal, byte-for-byte and case-sensitive; there are no wildcards, Unicode normalization, or token boundaries. Count each signature ID only once, regardless of repeated occurrences; for each matching ID record its **earliest zero-based byte start offset**.

Return exactly:

```json
{"request_id":"r-example","status":"ok","total_matching_signatures":2,"matches":[{"signature_id":"SIG-001","priority":80,"start":4},{"signature_id":"SIG-007","priority":40,"start":2}]}
```

The JSON above illustrates the response shape, **not fixture output**. Rank all eligible matching IDs by **priority descending**, then **earliest start ascending**, then **case-sensitive signature ID ascending**. Return the first `limit` matches; `total_matching_signatures` counts **all** matching eligible IDs even if there are more than `limit`. When none match, emit `total_matching_signatures:0,matches:[]` with `status:"ok"`. Output key names and result types must match the contract. Query order and repeated request IDs have no semantic effect.

## Observable acceptance criteria

- The `scan` command emits **one compact JSON object per physical query line**, in input order, with no diagnostic messages on stdout. Invalid queries never prevent subsequent queries from completing.
- Malformed JSON, non-object values, missing/invalid fields, wrong numeric types, oversized chunks/payload, noncanonical base64, or an invalid limit return `{"request_id":null,"status":"invalid","reason":"invalid_request"}`; preserve `request_id` when it has a valid ID format. A structurally valid query for a nonexistent region returns `status:"invalid",reason:"unknown_region"` and retains its request ID.
- A pattern may start at the final byte of one chunk and end in a later chunk. Empty chunks do not interrupt it. Adjacent chunks contribute **no artificial delimiter**.
- The matching is on raw bytes, not decoded UTF-8. NUL bytes, `0xff`, repeated byte sequences, and overlapping occurrences are valid. Match offsets count **bytes**, not characters or base64 positions.
- If several IDs share the same byte sequence, each eligible ID counts separately. A global signature and a regional signature may both match. Disabled, out-of-window, and other-region signatures never count.
- The time window includes its starting millisecond but excludes its ending millisecond. The winner is decided by ranking, not merely the first pattern found. Identical priority and start values use ID order.
- Multiple occurrences of one ID must contribute its **first start offset**. `total_matching_signatures` must not be truncated to `limit` and must not count duplicate catalog replays.
- Results must be deterministic across shuffled signature rows, different chunk boundaries for the same payload, repeated query IDs, and hash iteration orders.

## Constraints, scope and deliverable

Production can have **200,000 distinct signature IDs**, **5 million request bodies/day**, and a total signature-byte count around **4 million**, with highly repeated prefixes, suffixes, and short patterns. Most bodies are under 8 KiB but some reach the stated 1 MiB bound. Operators expect the catalog to be loaded once and then shared across a long stream of independent requests. Aim for roughly **1.5 GB working memory**, **p95 under 20 ms for ordinary bodies after loading**, and throughput that scales with the payload rather than scanning the full catalog on each request. These are engineering targets to justify and benchmark; the checked-in fixture is intentionally small. A naive separate substring scan for each signature on each request is not a credible production design.

In scope: snapshot validation, exact byte matching, eligibility, earliest offsets, ranking, bounded output, per-line error recovery, tests, complexity and memory analysis. Out of scope: network services, live signature updates, persistence, authorization, pattern inference, substring edits, decoding a particular application protocol, and any LLM API.

The provided catalog loader, JSON parser, CLI, small dataset and baseline tests are runnable. The scanning functionality is **deliberately not implemented**; a green starter suite does not establish matching correctness. Do not change fixtures to pass tests.

## Setup and verification

Python **3.11+**, standard library only. From the repository root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 signalgate.py check --regions fixtures/regions.csv --signatures fixtures/signatures.csv --requests fixtures/requests.jsonl
```

After implementing the scanner:

```bash
python3 signalgate.py scan --regions fixtures/regions.csv --signatures fixtures/signatures.csv --requests fixtures/requests.jsonl
```

## 60-minute AI-assisted interview instruction

**Timebox: 60 minutes.** Use Claude Code, Codex, ChatGPT, or another AI tool as you would on an actual customer issue. Inspect the fixtures and constraints, choose an approach, implement a correct slice, add targeted adversarial tests, run verification, and explain your design, correctness, memory/runtime bounds, and where the stated production targets might require more work. You must be able to defend any AI-generated code you retain.
