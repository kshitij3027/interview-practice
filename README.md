# ChronoCheck — HARD 60-Minute AI-Assisted Customer Interview

## Customer / business context

A logistics observability company receives diagnostics from barcode scanners, warehouse gateways and regional aggregators. Their clocks are not synchronized. Field technicians periodically measure how far one device's clock is ahead of another, but the export contains corrections, retried rows and occasionally impossible combinations. Incident analysts need trustworthy relative time offsets to correlate customer events. Returning a plausible but inconsistent offset can cause an incorrect incident timeline.

**Build one clock-calibration audit capability** that answers whether a pair of clocks has a uniquely supportable relative offset under the latest calibration snapshot. You choose the technical approach, including deterministic, heuristic, LLM-assisted or hybrid methods; you must defend how the choice meets exact correctness and scale requirements. No external SDK, API, network service or model key is required.

## Data supplied

- **fixtures/clocks.csv:** columns clock_id, tenant_id. Each device belongs to precisely one tenant. Identical declarations can repeat; conflicting declarations invalidate the whole catalog.
- **fixtures/measurements.csv:** columns measurement_id, revision, op, tenant_id, clock_a, clock_b, delta_us. Each measurement ID identifies one logical diagnostic that can be corrected or retracted. The highest numeric revision wins regardless of CSV order. An upsert asserts **clock_b reading minus clock_a reading equals delta_us**. A retract requires clock_a, clock_b and delta_us to be blank and contributes no current constraint. Retractions can appear before older revisions.
- **fixtures/requests.jsonl:** one independent audit per *physical line*, including invalid lines, repeated request IDs, and cross-tenant references.
- **chronocheck.py:** working snapshot ingestion, validation, CLI and unfinished ChronoCheck.assess(request) capability.
- **tests/** and **scripts/**: runnable starter checks, not the full customer acceptance suite.

Identifiers are case-sensitive ASCII letters, digits, underscore or hyphen, length 1–48; request IDs can have length 1–128. CSV headers must contain exactly the documented columns in any order. CSV numbers use canonical decimal notation: no leading zeros except zero, no plus sign, and no negative zero. Revisions lie in [1, 2000000000], and delta_us in [-1000000000000,1000000000000]. Intermediate *implied* differences may exceed this range and must not overflow.

A measurement ID must belong to one tenant across all revisions. Identical replays of the same (measurement_id,revision) are harmless, but conflicting copies invalidate the entire snapshot. All upserts, **including superseded ones**, must refer to declared clocks within their tenant. A bad catalog fails before any request output. A newer retraction removes a measurement; an older upsert printed later in CSV does not restore it. Identical different measurement IDs represent separate assertions.

## Primary customer request

Implement **ChronoCheck.assess(request)** and any justified preprocessing. Each request contains string fields request_id, tenant_id, source_clock, target_clock. All highest-revision *active* measurements are exact equations. Determine:

- **ok**: If a chain of active measurements relates the two clocks and *all equations in their connected calibration group* can hold simultaneously, return the unique signed difference, target clock reading minus source clock reading, as integer delta_us.
- **conflict**: If the pair is connected but their group has mutually incompatible measurements, return delta_us null. Do not guess, average or arbitrarily ignore any active measurement. This also applies to a request from a clock to itself if its group is contradictory.
- **unresolved**: If there is no chain relating the two clocks, return delta_us null even if one or both separate groups are contradictory. A source and target that are identical have offset zero *only when their group is consistent*, including isolated clocks.

Exact response shapes (illustrative values, not fixture answers):

    {"request_id":"example","status":"ok","delta_us":-150}
    {"request_id":"example","status":"conflict","delta_us":null}
    {"request_id":"example","status":"unresolved","delta_us":null}

Malformed JSON, non-object requests, missing or mistyped fields or invalid identifiers produce a result with status invalid, reason invalid_query, and request_id null unless a syntactically valid request_id can be recovered. A well-formed request referencing a clock undeclared **within its specified tenant** produces status invalid, reason unknown_clock; this includes clocks belonging to a different tenant. Extra JSON fields may be ignored. Duplicate request IDs are independent. Emit one compact JSON object per physical input line in original order, no progress output to stdout, and continue after malformed lines.

## Observable acceptance criteria

1. Signed orientation is exact: reversing the source and target reverses the offset in a consistent related group.
2. Use only each measurement ID's highest live revision, regardless of input ordering. Newer retractions remove earlier assertions.
3. Detect contradictions arising from several individually plausible assertions, including conflicting duplicates under different IDs and nonzero self-calibrations. Never hide a contradiction by selecting a convenient subset.
4. A contradiction affects only its own connected group; other groups in the same tenant and in different tenants remain independently auditable.
5. Disconnected pairs are unresolved. A self-request returns zero if consistent and conflict if inconsistent.
6. Preserve tenant isolation, case-sensitive IDs, duplicate request ordering and deterministic results independent of CSV row order or harmless retries.
7. Corrupt catalogs fail atomically, including conflicting revisions and invalid superseded records. Malformed individual requests are isolated.
8. Handle zero, negative and large exact integer offsets without floating-point approximation or overflow.

## Production constraints and tradeoffs

Fixtures are compact. Production has up to **1.5 million clocks**, **4 million measurement revision rows**, and **800,000 audit requests daily**. Many devices belong to large groups; some are isolated; hot pairs are queried repeatedly. Revisions are unordered, identifiers sparse, and some regions contain long or heavily redundant relationships. Target **about 1.5 GB working memory** and **p95 under 10 ms** for an ordinary audit request after one snapshot load; these are design targets, not fixture benchmarks.

Repeatedly scanning the entire calibration network or re-solving all relations for every audit is not credible. Explain preprocessing cost, query complexity, memory use, contradiction propagation, how you bound hot-query costs, and the alternatives you rejected. Exactness is required: heuristics cannot silently return unsupported values.

## Deliverable, scope and run commands

Implement the audit capability, add your own adversarial tests, and prepare a concise explanation of correctness, complexity and tradeoffs. Refactor if useful, but preserve the CLI and error contracts. Use **Python 3.11+ standard library only**. A database, UI, authentication, statistical drift estimation, clock synchronization protocol, online mutations, external SDK or third-party network service are out of scope.

From the branch root, verify the runnable baseline:

    bash scripts/build.sh
    bash scripts/test.sh
    bash scripts/verify.sh
    python3 chronocheck.py check --clocks fixtures/clocks.csv --measurements fixtures/measurements.csv

After implementing the capability, run:

    python3 chronocheck.py audit --clocks fixtures/clocks.csv --measurements fixtures/measurements.csv --requests fixtures/requests.jsonl

The starter deliberately reports **not_implemented** for valid requests. Passing starter tests demonstrates functioning scaffolding, *not* completion of the customer capability.

## 60-minute AI-assisted interview

**You have 60 minutes. Using Claude Code, Codex, ChatGPT or another AI tool is explicitly encouraged.** First inspect the actual data, contracts and scale, then choose and justify a strategy. Implement incrementally and validate with adversarial examples rather than a single AI prompt. Be ready to explain invariants, failure modes, time and space complexity and any AI-generated code you retained. A happy path without consistency and scale is not a complete solution.
