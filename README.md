# GridPulse — HARD 60-minute AI-assisted customer interview

## Customer / business context

An EV-fleet operator manages charging sites across multiple regions. The utility bills the operator partly on **peak instantaneous charging demand**, while planners also need the exact accumulated demand across arbitrary reporting windows. Every charger session contributes a constant measured draw in kilowatts during its recorded interval. The vendor's export contains late corrections, cancellations, replayed rows, and overlapping sessions. An analyst's spreadsheet scans all sessions for every new investigation window; it cannot keep up with the expected volume.

You own the approach, architecture, and tradeoffs. You may use deterministic, heuristic, LLM-based, or hybrid techniques, provided you can defend their accuracy, cost, and performance against the observable contract. No external account, API, model, or dependency is required.

## Supplied data

- `fixtures/sites.csv`: a `site_id` column. Site identifiers are 1–48 case-sensitive ASCII letters, digits, `_`, or `-`. Exact repeated site rows are harmless.
- `fixtures/sessions.csv`: `session_id,revision,site_id,mode,start_ms,end_ms,kw`. Each `session_id` represents one logical charging session and can have multiple revisions in **arbitrary file order**. A later numeric `revision` supersedes every earlier revision, even if the file lists it first. Revisions need not be consecutive. For an `upsert`, the site must exist, `0 <= start_ms < end_ms <= 10^12`, and `kw` is an integer `[0,100000]`. A later upsert can move a session between sites or change its time span or draw. For a `cancel`, all four value fields (`site_id`, `start_ms`, `end_ms`, `kw`) are blank. The highest revision determines whether the session contributes any power. A cancel with no preceding upsert is valid and contributes nothing. Identical replays of `(session_id,revision)` count once; conflicting reuse of that pair invalidates the **entire** catalog. Every individual row must validate even if later superseded.
- `fixtures/queries.jsonl`: one independent investigation per physical line, including intentionally invalid lines. A valid JSON object has `request_id`, `site_id`, `from_ms`, and `until_ms`. Request IDs follow the same ID format; unknown site IDs are invalid. The requested interval is nonempty `[from_ms,until_ms)`, with JSON integers in `[0,10^12]`. A boolean or numeric string is not an integer. Extra query fields may be ignored. Repeated request IDs are independent queries.

CSV columns can appear in any order; the supplied loader expects exactly the named columns. CSV integers must be canonical base-10 unsigned digits without leading zeroes (except `0`). Bad headers, malformed CSV, invalid references, invalid revisions, invalid intervals, and conflicting replays fail catalog load before processing any requests. Invalid JSONL queries are handled separately so later lines continue.

## Primary customer request

Implement `DemandSnapshot.evaluate(query)` in `gridpulse/engine.py`, changing other source files if useful. For each valid request, use the **latest revision per logical session** to determine charging activity at the requested site. A live session contributes its `kw` at every time `t` with `start_ms <= t < end_ms`; outside that interval it contributes zero. Overlapping sessions add their draws, including independent sessions with identical spans.

Return exactly the following shape (illustrative numbers, **not** a fixture answer):

```json
{"request_id":"example","status":"ok","site_id":"EAST-DEPOT","peak_kw":20,"peak_at_ms":250,"energy_kw_ms":7350}
```

- `peak_kw`: the maximum aggregate demand at any instant in the requested interval, including zero if the site is idle.
- `peak_at_ms`: the **earliest integer millisecond within the requested interval** where the maximum occurs. An idle window therefore reports `peak_kw:0` and `peak_at_ms:from_ms`.
- `energy_kw_ms`: the **exact integer integral** of aggregate demand over `[from_ms,until_ms)` in kilowatt-milliseconds, with partial sessions clipped to query boundaries. Do **not** convert it to kWh, round, or use floating-point arithmetic.

The interval is half-open throughout. A session ending at a query's start contributes nothing; one starting at its end contributes nothing. A session ending at the same instant another begins does not overlap that successor. Multiple sessions may peak at the same demand; the **earliest** qualifying time wins. No power is carried from one site to another except through an explicit latest-revision move.

## Observable acceptance criteria

- `assess` emits one compact JSON object per query line, in original order, with no diagnostics on stdout. Invalid JSON, invalid types/fields/IDs/timestamps, or zero-length windows produce `{"request_id":null,"status":"invalid","reason":"invalid_query"}`; preserve a valid request ID if recoverable. A structurally valid query for a nonexistent site instead uses `reason:"unknown_site"`.
- An upsert contributes on `[start_ms,end_ms)` at **only** its latest site. Later cancellations remove all contribution; earlier revisions never remain active alongside their replacements. Identical revision replays do not double-count.
- Adjacent sessions, simultaneous starts and ends, zero-draw sessions, duplicate time spans, and long idle periods produce exact peak and integral results without boundary spikes.
- A query starting **inside** a session can have its earliest peak at `from_ms`, not necessarily at any catalog event boundary. A window wholly before or after any activity returns a zero peak at `from_ms`.
- Accumulated demand can exceed 32-bit signed integer limits; maintain exact integer arithmetic. A site absent from the session feed is still queryable.
- Results do not change if session rows or query order are shuffled, repeated query IDs occur, or valid rows are replayed. Malformed queries must never poison subsequent requests.

## Scale and constraints

A production snapshot may contain **400,000 logical sessions**, **1.2 million revision records**, **300 sites**, and **300,000 investigation windows**. A few sites receive almost all sessions, and reports may span tiny intervals or the full 10^12-ms domain. The catalog is loaded once, while many unrelated queries arrive afterward. Target approximately **1.5 GB resident memory** and **under 20 ms p95** per typical query after preprocessing on a commodity host. These are engineering targets rather than fixture benchmarks. Re-scanning all sessions, sorting all events, or iterating every millisecond separately for each query is not a credible production strategy. Explain preprocessing costs, per-query complexity, and your worst-case behavior.

## Scope / out of scope

In scope: exact session-revision selection, per-site peak/earliest-peak/integral calculation, fast repeated arbitrary-window queries, robust catalog/query boundaries, and adversarial tests. The supplied input layer is functional and may be modified if your design requires it.

Out of scope: live charger control, energy tariffs, time-zone conversions, forecasting, authentication, deployment, databases, UI work, charging-station integration, and editing incoming sessions while a snapshot is being queried.

## Setup and verification

Python **3.11+**, standard library only. From the repository root:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 gridpulse.py check-inputs --sites fixtures/sites.csv --sessions fixtures/sessions.csv
python3 gridpulse.py assess --sites fixtures/sites.csv --sessions fixtures/sessions.csv --queries fixtures/queries.jsonl
```

The starter deliberately reports `not_implemented` on otherwise valid requests. Existing tests cover basic catalog parsing, request boundaries, and the callable interface; they are **not** a correctness oracle for the requested capability. Add focused tests. `scripts/verify.sh` verifies the unimplemented starter baseline and must be adapted after implementation.

## Your 60-minute AI-assisted interview

You have **60 minutes**. Use Claude Code, Codex, ChatGPT, or any other tools as you would in a real customer engagement. First inspect the supplied data and interfaces, select a defensible strategy, implement the most valuable correct slice, and test adversarial windows. Be ready to explain the behavior, time/space complexity, assumptions, failure modes, and any AI-generated code you chose to keep. The goal is a customer-worthy technical solution and sound judgment, not a memorized algorithm.
