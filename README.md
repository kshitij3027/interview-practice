# WaterLine — HARD 60-minute AI-assisted customer interview

## Customer / business context

A municipal water operator is asked to approve emergency repair plans. Before isolating up to two pipes, operators need to know how many **currently supplied** customer meters would lose access to **every** reservoir, plus the combined demand and count of critical-service meters. A spreadsheet prototype walks the entire distribution network for each proposed repair. It takes too long during a citywide incident and sometimes counts neighborhoods that already lack supply as a consequence of the repair.

Build a trustworthy **pipe-closure impact reviewer**. You decide the technical approach: deterministic, heuristic, AI-assisted, or hybrid, provided the numerical results are exact, reproducible, and defensible at production scale. This is one primary customer problem; no live valve control, external API, model key, or infrastructure deployment is required. Inspect the data and constraints before implementing.

## Supplied data and starter

- `fixtures/nodes.csv`: `node_id,source,meters,demand_lps,critical`. A node with `source=yes` is a reservoir that supplies water; all other nodes have `source=no`. `meters` is the number of customer meters aggregated at a junction; `demand_lps` is that junction's aggregate demand in liters/sec; `critical` counts critical-service meters among its customer meters. Source nodes have all three counts equal to zero.
- `fixtures/pipes.csv`: `pipe_id,a,b`. A pipe connects two nodes in **both directions**. Pipe IDs are unique physical controls. Several different pipes may connect the same endpoints. An endpoint can equal the other endpoint. Pipes do not have capacities, directions, time windows, or priority.
- `fixtures/requests.jsonl`: independent hypothetical repair reviews, one JSON object per **physical line**. The file includes meaningful closures, retries/duplicate request IDs, and intentionally invalid lines.
- `waterline.py`: catalog loader, query parser, CLI and unfinished `WaterLine.review(query)` capability.
- `tests/` and `scripts/`: working smoke tests and entry points. Starter tests are **not** the full acceptance suite.

CSV headers must contain exactly the named columns, in any order. IDs are case-sensitive ASCII letters, digits, underscores or hyphens, 1–48 characters long; request IDs may be 1–128 characters. CSV numeric fields are canonical unsigned integers (`0` or decimal digits without leading zeroes). `meters` and `critical` are in `[0, 1000000]`, `demand_lps` is in `[0, 1000000000]`, and `critical <= meters`. Source nodes require all counts to be zero. An identical repeated node or pipe row is a harmless delivery retry; conflicting reuse of an ID, malformed fields or headers, or unknown pipe endpoints invalidate the **whole catalog** before any request output. CSV row order does not matter.

## Required capability

Implement `WaterLine.review(query)`. A valid request looks like:

```json
{"request_id":"demo","close_pipes":["PIPE-03","PIPE-11"]}
```

`close_pipes` must be a JSON array containing **zero, one, or two** syntactically valid pipe IDs. Repeating the same pipe ID in that array closes it once. Every known pipe not in the closure set remains available, including pipes parallel to a closed pipe. Requests are independent simulations: **no closure persists into another request**. No water supply has a capacity limit: a node is supplied if there exists any traversable series of open pipes to **at least one** source node, regardless of how many sources or loops appear along the way. Every source is always active. Closed pipes cannot be traversed. A junction's demand cannot be partially supplied.

Compute the baseline supplied population using the **unmodified** catalog. For each request, calculate the set of nodes supplied before the closure but **not** supplied after the closure. Sum only those nodes' `meters`, `demand_lps`, and `critical` respectively. Nodes already unsupplied in the baseline are excluded from every impact result. A source has no counted meters; closing pipes that isolate a source may still affect other customer nodes. Do not count how many pipes were closed as impact.

Return **exactly** this JSON shape for each valid request (illustrative, not a fixture answer):

```json
{"request_id":"demo","status":"ok","affected_meters":12,"affected_demand_lps":25,"affected_critical":2}
```

For malformed JSONL lines or invalid request structure, emit `{"request_id":null,"status":"invalid","reason":"invalid_query"}`; retain the request ID instead of `null` if it is syntactically valid and recoverable. Validly structured requests referencing any unknown pipe use `reason:"unknown_pipe"`. Duplicate request IDs are **independent** reviews and must each produce their own line. JSON strings, booleans, floats, and numbers are not interchangeable types. Extra request keys may be ignored.

The CLI emits **one compact JSON object per physical request line**, in original order, with no logs on stdout. Catalog failures exit nonzero, print a useful stderr diagnostic, and emit **no partial request results**. You may refactor the starter while preserving these observable contracts.

## Observable acceptance criteria

- Removing either one or two known pipes returns exact, nonnegative meter/demand/critical losses compared to the original unmodified catalog. Removing zero pipes returns zero impact.
- Different reservoirs can supply the same network. A node counts as impacted only if **every** usable supply connection is lost; merely isolating one reservoir is insufficient.
- Parallel pipes are independent controls: closing one does not automatically close another. Self-connected pipes and disconnected islands are valid catalog data.
- Customer demand and critical counts are **per node**, not per pipe, and must never be double-counted when several possible paths or reservoirs reach a node.
- Closing the same pipe twice in one request is equivalent to closing it once. Repeating a request ID does not cache or mutate the hypothetical network state.
- Pipe and node catalog order, identical retry rows, and closure-array order must not change results. Missing or conflicting catalog references are fatal; malformed or unknown-pipe requests are isolated from later lines.
- A pre-existing isolated customer island must not inflate closure impact, even if the repair disconnects a different part of the network.
- Outputs must use exact integer arithmetic and deterministic JSON field meanings for large numbers and small edge cases.

## Production constraints

The small fixtures deliberately include multiple reservoirs, overlapping routes, parallel pipes, an isolated legacy sector, repeated deliveries, and unhelpful links. Production snapshots may contain **250,000 junctions**, **500,000 independently controlled pipes**, and **75,000 separate repair reviews** per batch, each closing at most two pipes. Networks can have very skewed high-degree junctions, long chains, many redundant loops, isolated islands, and many reviews targeting the same two controls. Aim for **under 768 MB peak working memory and under 45 seconds for a typical batch after parsing** on a modern worker. These are scale-design targets, not measured fixture benchmarks. Rebuilding/traversing the full network per request is not a credible strategy; explain initialization cost, query/batch complexity, worst cases, and memory tradeoffs.

## Deliverable, scope, and verification

Use Python 3.10+ standard library; no dependencies or accounts are required. Implement the review capability and any necessary preprocessing or batch strategy while preserving the CLI contract. Add your own targeted tests for hard cases and use the fixture to inspect whether outputs make sense. A technically justified partial solution plus clear scalability discussion is better than silently claiming the placeholder is correct.

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 waterline.py --nodes fixtures/nodes.csv --pipes fixtures/pipes.csv --requests fixtures/requests.jsonl
```

The repository **starts with a runnable placeholder**: green tests demonstrate parsing, validation, and CLI wiring, but **do not validate the nontrivial impact logic**. Your task is to replace that placeholder. Out of scope: pressure modeling, pipe flow capacities, repair duration, supply failures, changing catalog between requests, user interface, and external services.

**60-minute AI-assisted interview:** You may use Claude Code, Codex, ChatGPT or other tools as you would on the job. Spend the first few minutes inspecting the fixtures and constraints; choose and articulate your own approach, implement an increment, validate meaningful examples, and be prepared to defend correctness, complexity, failure modes, and any use of AI. The interviewer assesses your problem-solving and verification, not whether an LLM wrote your code.
