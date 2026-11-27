# ReviewDesk — Localization review coverage

**HARD · 60-minute AI-assisted customer interview · Node.js 20+**

## Customer message

> Our localization agency has one shift to review translated customer documents before delivery. A separate routing service supplies the reviewers qualified for each document, taking language, certification and conflicts of interest into account. A reviewer can review several documents, but has a fixed shift quota. Our spreadsheet assigns the first available reviewer and frequently leaves documents uncovered even when a different assignment could cover them. We need a defensible coverage plan for each shift, particularly when senior reviewers are scarce.

Build ONE shift coverage planner. Choose your own approach (deterministic, heuristic, AI-assisted or hybrid); the observable requirements are the same. Use Claude Code, Codex, ChatGPT or other tools as on the job. Inspect the data, implement incrementally, verify the result and explain your decisions within 60 minutes. No external services or credentials are required.

## Supplied data and starter

`fixtures/batch.json` is one complete shift snapshot. `reviewers` contains objects with `id`, `queue`, `capacity` (number of documents the reviewer may take). `documents` contains objects with `id`, `queue`, `priority` (1 lowest, 5 highest), and `eligible` (array of reviewer IDs from the upstream routing service). Queues are independent; the same reviewer cannot serve two queues. Every document takes one unit of capacity and must have exactly one reviewer or remain uncovered. Review quality is already represented by eligibility; do not infer eligibility from IDs.

`catalog.mjs` validates and normalizes the snapshot; `planner.mjs` contains the unfinished `plan(batch)` interface; `cli.mjs` is the executable entry point. The baseline CLI reports `not_implemented` for valid data until you build the planner.

IDs and queue names are case-sensitive ASCII letters, digits, underscore or hyphen, 1–48 characters. Capacities are JSON integers 0..300; priority is a JSON integer 1..5. Repeated reviewer/document declarations are allowed only if their normalized fields are identical (eligibility is a set; order and duplicates are irrelevant). Conflicting declarations, unknown eligible IDs, cross-queue eligibility, invalid types/ranges and malformed JSON reject the entire input, with nonzero exit and stderr, before any stdout. Extra fields are ignored. Empty eligibility, empty queues and zero capacities are valid. Input row order carries no business meaning.

## Primary request

Implement `plan(batch)` in `planner.mjs` and any supporting code. Each reviewer may take at most their capacity and only eligible documents. A document may never be split or assigned twice. Choose a plan that satisfies these objectives in strict order:

1. Maximize the total number of covered documents.
2. Among plans with that coverage, prefer the plan covering the first differing document when documents are ordered by priority descending, then ID ascending (case-sensitive ASCII order). That is, compare the covered/not-covered decisions in that order, preferring covered at the first difference. This is not a sum of priorities.
3. For the same covered set, any valid reviewer assignment is acceptable, but the exact output must be deterministic under input row and eligibility-list permutations.

Return an object shaped like:

```json
{"status":"ok","covered_count":2,"assignments":[{"document_id":"D1","reviewer_id":"R2"},{"document_id":"D3","reviewer_id":"R1"}],"uncovered":["D2"]}
```

The example is illustrative, not a fixture answer. `assignments` is sorted by document ID, `uncovered` by document ID. Every document appears exactly once across the two arrays. `covered_count` equals assignments length. For no documents, return zero and two empty arrays. Every run starts from the given snapshot; never mutate the input or retain allocations between invocations.

## Production envelope

Up to 30,000 documents, 10,000 reviewers, 20 distinct eligible reviewers per document, and 300 documents and 100 reviewers per queue. Many queues have scarce reviewers and several documents with overlapping options. Quotas may be much larger than actual demand. Target a complete shift plan within 8 seconds and 256 MiB heap on a typical laptop; measure a generated representative workload and discuss worst-case behavior. Do not enumerate all possible assignments. The checked-in sample is small on purpose. No requirement to optimize for unbounded queue sizes.

## Scope and verification

Deliver the working planner and your own focused tests; preserve the CLI and catalog behavior. Out of scope: UI, persistent scheduling, reviewer availability changes during the shift, translation itself, and network integration. No npm install required.

```sh
node --check catalog.mjs && node --check planner.mjs && node --check cli.mjs
node --test tests/*.test.mjs
node cli.mjs fixtures/batch.json
```

The starter checks validate ingestion and the CLI, not all acceptance criteria. At the end of the hour, demonstrate the output, explain why it is globally valid, discuss scale and tradeoffs, and identify any incomplete behavior.
