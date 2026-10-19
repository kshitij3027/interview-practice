# SatLink — HARD 60-minute AI-assisted customer interview

## Customer/business context
A satellite telemetry provider receives partial binary exports through unreliable gateways. Retries, out-of-order fragments, overlaps, and missing byte ranges make reconstruction difficult. Operators need to know which exports are trustworthy, what captured bytes they can read, and the first missing or contradictory location. The current prototype allocates the advertised export size and rescans captures for every query; production data makes that infeasible. Build an exact in-process auditor for one immutable snapshot.

## Supplied data
- fixtures/manifests.csv: asset_id,size,expected_sha256. IDs are 1–48 case-sensitive ASCII letters/digits/underscore/hyphen. Size is an integer 0..10^12 inclusive. Digest is a 64-character lowercase hexadecimal SHA-256 or * (no expected digest). Identical replays of a manifest are harmless; conflicting definitions are fatal.
- fixtures/fragments.jsonl: each line contains capture_id,asset_id,offset,payload_b64. IDs follow the manifest ID rule. Offset is a zero-based integer; payload is 1..65536 decoded bytes of canonical padded base64. The fragment must fit in a known asset. Identical replay of a capture_id counts once; conflicting reuse is fatal. Different capture IDs may overlap, even completely.
- fixtures/queries.jsonl: each line is an independent status or read query. All have request_id,asset_id,kind; read additionally has start and end. IDs obey the same format and request IDs may repeat. Half-open read ranges [start,end) allow empty reads but at most 4096 bytes. Offsets must be nonnegative integers (not booleans), <=10^12, inside the asset. Extra query fields are ignored.

Example requests (JSONL):
{"request_id":"q1","asset_id":"A-STRIP","kind":"status"}
{"request_id":"q2","asset_id":"A-STRIP","kind":"read","start":0,"end":5}

## Primary customer request
Implement AuditEngine.answer(request) in replay_engine.py and any supporting code/tests. The validated loader and CLI in uplink.py work already, but the audit engine is deliberately absent. Choose the implementation strategy; whether deterministic, heuristic, LLM-based or hybrid, results must be exact.

Compute unique observed byte count covered_bytes (overlaps never count twice), first_missing_offset (smallest absent byte in [0,size), or null), and the minimum conflicting offset conflict_at across all disagreements between overlapping captures. Capture arrival order may not change answers. Each asset has one status, in this priority: corrupt if ANY overlap disagrees, even if incomplete; partial if any byte is missing but no disagreement; checksum_mismatch if fully captured and conflict-free but SHA-256 differs from expected; complete otherwise. Hash raw bytes in offset order, including for empty assets. sha256 is null for partial/corrupt assets; otherwise it is the observed lowercase digest. A digest of * imposes no checksum comparison. Disagreements affect only their own asset.

## Observable output / acceptance criteria
Write one JSON object per query line, in original order; diagnostics only to stderr. For valid status requests return exactly request_id,asset_id,status,size,covered_bytes,first_missing_offset,conflict_at,sha256. For example, this illustrates shape only and is not a fixture answer:
{"request_id":"q","asset_id":"sample","status":"partial","size":20,"covered_bytes":7,"first_missing_offset":7,"conflict_at":null,"sha256":null}

For read [start,end): if the asset is corrupt or checksum_mismatch, return request_id,asset_id and that status (no data). Otherwise, if ALL requested bytes are captured, return status=available and data_b64 containing exact canonical base64 for the range (including empty range). If any byte is missing return status=missing and first_missing_offset set to the first missing offset WITHIN the read interval. All read results include request_id and asset_id.

Malformed JSON, invalid request fields, or an out-of-asset read return status=invalid,reason=invalid_request; preserve request_id only when a valid ID exists in the parsed request object, otherwise null. Valid queries for unknown assets instead use reason=unknown_asset. Continue after bad queries. Invalid manifests/fragments, noncanonical base64, conflicting replay IDs, and out-of-range fragments fail the entire snapshot before processing queries, with nonzero exit and stderr message.

Handle identical and conflicting overlaps, nested/disordered/adjacent fragments, globally earliest conflict, repeated capture IDs, zero-length exports, huge sparse sizes, binary payloads, reads crossing holes, readable islands of partial assets, SHA mismatch blocking reads, duplicate request IDs, boolean offsets, and shuffled input order.

## Constraints and scope
Production: up to 800,000 assets, 8 million fragments, 4 million queries, and 700 MB delivered payload; asset size up to 10^12 even if almost empty. Target roughly 1.5 GB RAM and under 3 ms typical p95 per query after preprocessing. These are engineering goals to assess, not tested fixture guarantees. Avoid dense allocation by declared size and avoid scanning all captures for every query. In scope: exact audit/reads, verification, failure handling, scalability reasoning. Out of scope: networking, auth, encryption, persistent storage, UI, guessing missing bytes.

## Setup and verification
Python 3.11+, standard library only. Run:
    bash scripts/build.sh
    bash scripts/test.sh
    bash scripts/verify.sh
    python3 uplink.py validate --manifests fixtures/manifests.csv --fragments fixtures/fragments.jsonl --queries fixtures/queries.jsonl
After implementing:
    python3 uplink.py audit --manifests fixtures/manifests.csv --fragments fixtures/fragments.jsonl --queries fixtures/queries.jsonl
Baseline tests verify loading and CLI, NOT the absent audit capability or full acceptance criteria.

## 60-minute AI-assisted interview instruction
You have 60 minutes. Use Claude Code/Codex/ChatGPT as on a customer escalation. Inspect data, choose and implement an approach, add adversarial tests, verify outputs, and defend correctness, complexity, memory, failure handling and whether deterministic, heuristic, LLM or hybrid techniques fit.