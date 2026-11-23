# ProofSpan — Independent Monitoring Evidence Audit

**HARD · 60-minute AI-assisted customer interview · Python 3.11+**

## Customer message

> We run facilities where independent monitoring vendors verify that essential infrastructure is healthy. Different probes, operated by the same vendor, often submit overlapping healthy intervals. After an outage, customers ask: "During this exact audit window, for how long could at least three independent vendors verify the service? And if the requirement was not met, when did those gaps start and how long were the worst gaps?"
>
> Our export arrives with late corrections, exact duplicate deliveries and withdrawals. The current analyst script checks every observation against every audit window and sometimes counts multiple probes from one vendor as independent witnesses. We have too many audit windows for this to work reliably.

Build **one audit capability** that answers these requests exactly. Choose your own solution strategy and be prepared to justify it; deterministic, heuristic, LLM-assisted or hybrid designs are acceptable only if they satisfy the same observable correctness, latency and resource requirements. No external service, model, SDK, credentials or network access is needed.

## Inspect the supplied data first

- `fixtures/scopes.csv` — `scope_id,site_name`. A scope is a facility area. The site name is only display metadata. An area may have zero probes.
- `fixtures/probes.csv` — `probe_id,scope_id,vendor_id`. A probe belongs to one scope and one independent monitoring vendor. A vendor may operate **multiple probes at the same scope**, and the same vendor ID may appear at other scopes.
- `fixtures/observations.csv` — `observation_id,revision,op,probe_id,start_ms,end_ms`. Each upsert attests that the named probe reported healthy throughout the half-open interval `[start_ms,end_ms)`. Retracts cancel the logical observation. Revisions and rows are **not** guaranteed to arrive in order.
- `fixtures/audits.jsonl` — one independent audit per **physical line**, with deliberately invalid requests and repeated audit IDs.
- `coverguard.py` — runnable catalog validation, request validation, CLI and the deliberately unfinished `CoverageAudit.evaluate(audit)` method. `scripts/` and `tests/` supply green starter verification, not the customer acceptance suite.

The catalogs are snapshots, not streams to replay during a request. Choose any preprocessing you need while keeping the CLI contract.

## Catalog contract

CSV headers must contain **exactly** the named columns (in any order). Identifiers are case-sensitive ASCII letters, digits, `_` or `-`, length 1–48; `audit_id` may be length 1–128. `site_name` is 1–80 printable ASCII characters. CSV integers must use canonical **unsigned decimal** (`0` or no leading zeros), never a sign, whitespace, float or scientific notation. Revisions are 1..2,000,000,000. Timestamps are integer milliseconds in `[0,1,000,000,000,000]`.

An `upsert` row must reference a declared probe and satisfy `start_ms < end_ms`. A `retract` row has **blank** `probe_id,start_ms,end_ms` and is valid even without an earlier upsert. Every observation ID's **highest numeric revision** is authoritative. It replaces earlier data completely or retracts the observation; an older revision appearing later in the CSV does not revive it. Observation IDs may change their associated probe in a later upsert. All upserts, including superseded ones, must be well formed and reference known probes.

Identical repeated scope/probe rows and **identical** copies of the same `(observation_id,revision)` are harmless retries, not additional evidence. A conflicting repeated ID or revision, malformed row, unknown catalog reference or invalid field must reject the **entire catalog** before emitting *any* audit output. Catalog order is otherwise irrelevant.

## Primary capability

Implement **`CoverageAudit.evaluate(audit)`** in `coverguard.py`, plus justified setup/indexing. An audit has the following shape:

```json
{"audit_id":"review-17","scope_id":"EAST","from_ms":5,"until_ms":35,"min_vendors":2}
```

`audit_id` and `scope_id` must be valid identifiers. `from_ms` and `until_ms` must be **actual JSON integers**, with `0 <= from_ms < until_ms <= 1000000000000`. `min_vendors` must be an **actual JSON integer** in `[1,4]`. Python booleans, JSON floats and numeric strings do not count as integers. Additional JSON object fields may be ignored. Duplicate audit IDs are independent requests.

At a time `t`, a vendor is a valid witness for a scope if **at least one** probe belonging to that vendor and scope has an observation whose *latest revision is an upsert* and whose interval contains `t` (`start_ms <= t < end_ms`). A vendor contributes **exactly one witness**, regardless of the number of simultaneous probes or observations. Vendors active in another scope do not count. Evidence is exact: do not infer health through missing periods, expand endpoints or allow time tolerances.

A timestamp is **covered** if the number of distinct witnessing vendors at that timestamp is at least `min_vendors`; otherwise it is **uncovered**. Evaluate the full audit window `[from_ms,until_ms)`, including times with no observations. Return exactly these fields for each valid known-scope audit:

```json
{"audit_id":"review-17","status":"ok","covered_ms":12,"first_gap_ms":5,"longest_gap_ms":8,"gap_count":2}
```

Those numbers illustrate **JSON shape only**, not the result for the example. Define:

- `covered_ms`: exact total duration in milliseconds within the window where the vendor minimum holds.
- `first_gap_ms`: the **earliest timestamp** in the window that is uncovered, or `null` if all of it is covered.
- `longest_gap_ms`: the duration of the **longest continuous uncovered subinterval** after clipping to the audit window, or `0` when fully covered.
- `gap_count`: the number of **maximal nonempty contiguous uncovered subintervals** within the audit window. Adjacent uncovered slices without a covered slice between them form **one** gap, even when observation endpoints occur between them.

Treat intervals as continuous half-open ranges of integer-millisecond coordinates: e.g. `[2,5)` contributes `3` milliseconds of duration. The query window can start or end *inside* a gap or a covered span; only its intersection with the audit window counts. The time domain may be extremely sparse.

## Error behavior

For malformed JSON, empty physical lines, missing/wrong fields or types, invalid identifiers or numeric bounds, output exactly:

```json
{"audit_id":null,"status":"invalid","reason":"invalid_audit"}
```

Keep a non-null `audit_id` if its value is a syntactically valid audit ID even when other fields are invalid. A **structurally valid** audit for an undeclared scope instead returns `{"audit_id":"review-17","status":"invalid","reason":"unknown_scope"}`. Validate structure before scope existence. Bad audits must not affect subsequent audits.

Emit **one compact JSON object per physical input line**, in the original order, without progress messages on stdout. The CLI should exit nonzero and report a useful message to stderr for bad catalog files; it must not print any partial JSONL on catalog failure. The supplied CLI already handles these boundaries. The method currently returns a placeholder for valid requests; your implementation replaces it with the required `ok` response.

## Observable acceptance criteria

- Deduplicate evidence from multiple probes and observations from the **same vendor** at the same scope; two distinct vendors count twice, even if the same organization operates many probes elsewhere.
- Use only each observation's latest revision; honor corrections, retractions, out-of-order rows and harmless exact retries. An updated observation may move to another probe.
- Apply **half-open** boundaries precisely. At an observation's `end_ms`, it no longer witnesses; at `start_ms`, it does. Simultaneous starts and ends do not create artificial duration.
- Count covered duration exactly for each possible `min_vendors` of 1..4. A scope with fewer independent vendors than requested, or a scope with no probes, can have a fully uncovered window.
- Return the earliest uncovered instant, *longest* contiguous uncovered duration and correct number of gaps, including when the audit window clips the middle of one or more gaps.
- Merge touching uncovered periods into one gap even if a record boundary, expired/restarted probe, or vendor handoff occurs in between and the minimum was never reached.
- Use exact integer arithmetic on enormous sparse timestamps. Return `null`, zero and counts correctly for fully covered, fully uncovered and partially covered windows.
- Keep scopes isolated, preserve deterministic output regardless of input row order or repeated audit IDs, and isolate invalid audit lines; reject bad catalogs atomically.

## Production scale and scope

Compact fixtures represent up to **2,000,000 observation revisions**, **250,000 probes**, **18,000 scopes** and **300,000 independent audit windows** per batch. A handful of scopes dominate volume. Some vendors operate thousands of probes and generate heavily overlapping intervals; windows can span essentially the whole 1e12 ms timestamp domain. Aim for **approximately 1.5 GB working memory** and **under 50 ms p95 for typical audits after initialization** on commodity hardware; these are design targets rather than requirements enforced by starter tests. Per-audit scanning of all raw observations is not production-ready.

**In scope:** correctly resolving the fixed snapshot, answering each audit independently, meaningful focused tests, and defending initialization, query cost, worst-case behavior and the chosen technology. **Out of scope:** live ingestion, storing or retrieving data from remote services, dashboards, handling untrusted signatures, or changing the definition of an independent vendor.

## 60-minute AI-assisted interview

**Use AI tools freely** (Claude Code, Codex, ChatGPT, or other tools) as you would while solving a real customer issue. Spend the hour inspecting data, picking a strategy, implementing the highest-value behavior, deriving focused tests and reviewing outputs. In the walkthrough, explain which correctness invariants your approach enforces, why it scales better than a naive scan, what you verified and what remains unfinished. You own the design, not the AI assistant.

Run from the repository root on Python 3.11+; **standard library only**:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 -B coverguard.py --scopes fixtures/scopes.csv --probes fixtures/probes.csv --observations fixtures/observations.csv --audits fixtures/audits.jsonl
```

Use `--audits -` to read from stdin. The starter checks test infrastructure and data validation; they **do not** prove the business algorithm has been implemented. Add your own correctness cases.
