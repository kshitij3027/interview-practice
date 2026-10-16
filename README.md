# FiberWatch — 60-minute AI-assisted systems interview

## Customer context
A fiber operator needs to understand which customer locations would lose service if one physical fiber span failed. The current procedure independently searches the whole network for each cable, which cannot support production incident traffic. Build a **read-only analyzer for one immutable network snapshot**. Choose the implementation strategy; deterministic, AI-assisted, heuristic, or hybrid approaches are yours to defend against the correctness requirements.

## Supplied data
- `fixtures/sites.csv`: `site_id,kind,active_accounts,priority_accounts`. Kind is `core`, `exchange`, or `access`. Cores provide connectivity, exchanges are intermediate facilities, and only access sites may have nonzero counts. Counts are nonnegative, priority cannot exceed active, and an access site with zero accounts still counts as a location. Site IDs are unique and case-sensitive; at least one core is required.
- `fixtures/spans.csv`: `span_id,site_a,site_b,enabled`. Each row identifies one independent undirected physical span between known sites; `enabled` is exactly `true` or `false`. Two distinct span IDs may join the same endpoints, and self-connections are valid. Identical duplicate rows for the same ID are harmless retries; conflicting reuse of an ID fails snapshot validation. Disabled spans carry no service.
- `fixtures/requests.jsonl`: one request per line. `{"request_id":"q1","type":"span","span_id":"S-06"}` or `{"request_id":"q2","type":"top","limit":5}`. Request IDs must be nonempty strings and may repeat independently. A top limit is integer 1–50, not boolean. Extra request fields are ignored.

## Primary customer request
A site is **served** if it reaches **any** core through enabled spans. Simulate removing exactly one requested span ID, without removing a parallel span. A **newly disconnected** site was served before this outage but is unable to reach any core afterward. Count only newly disconnected access sites, their active accounts, and their priority accounts. Sites already unserved, exchanges, and cores contribute nothing. A disabled span has zero outage impact.

Implement `NetworkAssessment.assess(...)` in `netops/resolver.py` and any helpers/tests needed. For a `span` query, return `request_id,status:"resolved",span_id,impacted_sites,impacted_accounts,impacted_priority_accounts` with exact nonnegative counts. For a `top` query, return `request_id,status:"resolved",spans`, an array of at most `limit` entries with those same impact fields, excluding disabled spans. Include zero-impact enabled spans if needed.

Order top entries by **descending priority accounts, descending total accounts, descending impacted access-site count, then lexicographically ascending case-sensitive span ID**. All results must be independent of site/span row ordering.

## Acceptance criteria and traps
Produce one JSON object per request line, in original order, with no diagnostics on stdout. Invalid JSON or invalid request fields emit `{"request_id":null,"status":"invalid","reason":"invalid_query"}`, preserving a nonempty string request ID when supplied. A known-shape span request for a nonexistent ID returns `status:"invalid",reason:"unknown_span"`. Continue after per-request failures. Invalid snapshot data must fail fast with a useful stderr diagnostic and nonzero exit code.

Discover and handle multiple cores, alternate paths, parallel physical spans, cycles, disabled spans, self-connections, already-unserved islands, zero-account locations, duplicate deliveries, tie-breaking, repeated queries, and malformed inputs. A failure may disconnect zero subscribers but still lose one access site.

## Production constraints
The supplied fixture is small; production has up to **2 million sites, 5 million spans, and 1.5 million requests** on the same immutable snapshot. Typical requests assess one span, while some request a top 50. Target after preprocessing: p95 under 2 ms per span and 30 ms per top-50 request, about 1.5 GB memory. Rebuilding reachability for every potential span or query is not acceptable. Explain complexity, memory, correctness, and which Python SLAs require empirical validation.

## Scope / expected deliverable
In scope: exact single-span outage impacts, ranked highest-risk span listing, snapshot validation, query recovery, verification tests, and explainable scaling decisions. Out of scope: multi-span failures, capacity and optical modeling, live topology changes, databases, authentication, networking services, and UI.

## Setup and verification
Python 3.11+, no external dependencies:

```bash
bash scripts/test.sh
bash scripts/build.sh
bash scripts/verify.sh
```

After implementing the analyzer:

```bash
python3 fiber_ops.py assess --sites fixtures/sites.csv --spans fixtures/spans.csv --queries fixtures/requests.jsonl
```

## 60-minute AI-assisted interview instruction
Use Claude Code, Codex, ChatGPT or similar AI tools as on a real customer issue. **You have 60 minutes.** Inspect the dataset and constraints, choose an approach, implement incrementally, add focused tests, and explain your tradeoffs. A solution that works only on the fixture but scales linearly with the full network on every lookup is incomplete.
