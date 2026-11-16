# SourceMark — HARD 60-Minute AI-Assisted Customer Interview

## Customer / business context

A packaged-food manufacturer combines ingredient lots into production sampling mixes. When lab screens find a contamination marker, quality managers need the **smallest plausible set of supplier lots** that explains every positive and negative result. Guessing the first lot in a positive sample can trigger unnecessary recalls or miss a plausible source. Build **one reliable source-attribution capability** using a fixed ingredient and sampling catalog. You own the technical solution; deterministic, heuristic, AI-based or hybrid approaches are acceptable if they satisfy the exact contract. No external services, account or lab knowledge is required.

## Supplied data

- `fixtures/lots.csv`: `lot_id,site,ingredient`. A lot belongs to exactly one plant; ingredient names are descriptive, not shortcuts.
- `fixtures/mixes.csv`: `mix_id,site`. A declared mix may contain zero lots.
- `fixtures/membership.csv`: `mix_id,lot_id`, one relation per contributing supplier lot. Lots may appear in multiple mixes and mixes may overlap.
- `fixtures/requests.jsonl`: separate screening investigations, including malformed examples.
- `sourcemark/catalog.py`, `sourcemark/contracts.py`, `sourcemark/cli.py`, `sourcemark/engine.py`, `tests/` and `scripts/`: working loading, parsing, CLI and starter verification, but **not** the finished attribution feature.

CSV headers must contain exactly their documented columns, in any order. Lot, mix, site and ingredient IDs use case-sensitive ASCII letters/digits/underscore/hyphen, length 1–48. Identical duplicate declarations and memberships are harmless delivery retries. Conflicting declarations, unknown references, cross-site membership, or malformed records invalidate the **whole catalog before any request output**. An empty mix is valid and has no membership rows. CSV ordering has no meaning.

## One primary customer request

Implement `SourceAttributor.assess(request)` and any justified indexing/preprocessing. A request is an independent hypothetical investigation:

```json
{"request_id":"case-01","site":"OAK","max_sources":2,"readings":[{"mix_id":"MX-O1","result":"positive"},{"mix_id":"MX-O2","result":"negative"}]}
```

`request_id` is 1–128 case-sensitive ASCII ID characters. `site` must be declared. `max_sources` is an **actual JSON integer** 0..3, not a boolean, float or string. `readings` contains 0..40 objects, each with a valid `mix_id` and `result` of exactly `"positive"` or `"negative"`. All referenced mixes must belong to the request site. Repeated identical readings for one mix are harmless; conflicting readings invalidate that request. Extra fields may be ignored. Repeated request IDs are independent and are not a deduplication key.

A source lot is either contaminated or not, consistently across the investigated mixes. Under this simplified model, each positive mix **must contain at least one chosen lot**; each negative mix **must contain no chosen lot**. There are no false test results, dilution effects, concentrations, or external contamination. Only lots declared at the request site may be chosen.

Consider all **distinct sets of lots** of size at most `max_sources` that satisfy every reading. Choose a set with the **fewest lots**. If several equally small source sets exist, choose the one whose **sorted case-sensitive lot-ID array** is lexicographically smallest. Set `ambiguous:true` iff at least **two different** source sets attain this *minimum number* of lots, not just if a more expensive explanation also exists.

Successful response (illustrative values, not a fixture answer):

```json
{"request_id":"case-01","status":"ok","sources":["LOT-A01"],"count":1,"ambiguous":true}
```

If no source set satisfies all readings within the cap:

```json
{"request_id":"case-01","status":"no_match","sources":[],"count":null,"ambiguous":false}
```

If there are **no positive readings**, the empty set is the **unique minimum explanation**, even with negative readings or no readings.

Malformed JSONL lines or request structure yield `{"request_id":null,"status":"invalid","reason":"invalid_query"}`, with a syntactically valid request ID retained if recoverable. Unknown sites use `reason:"unknown_site"`; unknown mixes use `"unknown_mix"`; mixes declared for a different site use `"wrong_site"`. An invalid query must not affect later requests. Emit one **compact JSON object per physical JSONL input line**, in original order, with no diagnostics on stdout. Catalog failures must exit nonzero, report stderr, and produce no partial JSONL.

## Observable acceptance criteria

- A positive empty mix is infeasible; a negative empty mix imposes no restriction.
- Minimum number of **distinct** lots is the primary objective. The source array is sorted and case-sensitive lexicographic tie-breaking is deterministic.
- At cap 0, no positive results is solvable and any positive nonempty mix is not. JSON `true`, `2.0` and `"2"` are not valid `max_sources:2`.
- Count distinct optimum source sets for ambiguity; duplicated CSV rows and repeated identical readings do not count as alternative explanations.
- Resolve overlapping mixes, negative eliminations, lots absent from all selected positive mixes, and contradictions across *different* mixes correctly.
- Contradictory duplicate readings are an invalid request; a logically inconsistent but structurally valid set of different readings returns `no_match`.
- Site boundaries, unknown IDs, malformed requests, CSV row-order independence, repeated IDs, and catalog-level atomic failure all matter.
- Return globally correct results for source counts 0, 1, 2 and 3 without choosing a plausible but non-minimum explanation.

## Production constraints and design tradeoffs

Fixtures are compact; production can have **200,000 lots, 150,000 mixes, 2 million memberships, and 30,000 investigations** per batch, with up to 40 mix readings per investigation and a maximum of three sources. Membership is highly skewed, many supplier lots have identical mix participation, and popular mixes are reused across many investigations. Target **under 768 MB** memory and **p95 under 150 ms for typical requests after catalog load** (engineering targets, not local benchmarks). Brute-force trying all combinations of every lot per query will not scale. Explain initialization cost, query work, worst-case combinatorics, indexing/reuse, and how a small exhaustive oracle could validate your algorithm.

## Deliverable, run commands, scope

Use **Python 3.11+ standard library only**. Implement attribution and meaningful focused tests; be prepared to explain correctness, complexity and failure modes. You may refactor without breaking the observable CLI or error contracts. Out of scope: a browser UI, real-world recall action, probabilities, false-positive lab screens, live catalog edits, external SDKs, or authentication.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 sourcemark.py check --lots fixtures/lots.csv --mixes fixtures/mixes.csv --membership fixtures/membership.csv
```

After implementation, execute:

```bash
python3 sourcemark.py assess --lots fixtures/lots.csv --mixes fixtures/mixes.csv --membership fixtures/membership.csv --requests fixtures/requests.jsonl
```

The starter returns `not_implemented` for structurally valid investigations. Passing the initial green tests is **not** customer acceptance.

## The 60-minute AI-assisted interview

**You have 60 minutes and AI use is explicitly encouraged.** Use Claude Code, Codex, ChatGPT or similar tools as you would on a real customer issue. Inspect the catalog and constraints, identify ambiguities, choose and implement an approach incrementally, test adversarial examples, and defend the behavior, time/space complexity, tradeoffs, failure modes, and AI-generated code you accepted.
