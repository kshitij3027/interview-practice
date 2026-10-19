# QuoteScope — HARD 60-minute AI-assisted systems interview

## Customer and business context
A wholesale components marketplace receives competing bid and ask quotes from participating dealers. Dealers replace their available lot counts and sometimes change prices; gateways replay updates and deliver messages out of order. Purchasing operators need exact historical executable price estimates for an order at any millisecond in the captured session. Their existing implementation replays every update and scans all dealer quotes for each estimate, which fails under production traffic.

## Supplied data
`fixtures/updates.csv` contains `update_id,received_ms,sequence,market,quote_id,side,price_cents,available_lots`. A row **sets** one dealer quote's absolute available quantity and price (it is not a delta). The same `quote_id` always belongs to one `market` and one `side` (`ask` or `bid`); its price may change. Zero lots removes the quote from executable depth until a later update restores it. All money is integer cents; no floats.

Event timestamps are nonnegative integer milliseconds since the start of the capture, up to 10^12; `sequence` is a nonnegative integer, and a `(received_ms,sequence)` pair uniquely orders distinct updates. At the same millisecond, apply smaller sequences first. `update_id`, `quote_id`, and `market` are case-sensitive ASCII letters/digits/underscore-hyphen, length 1–48. IDs and numeric fields are validated by the supplied loader. Identically replayed `update_id` rows count once; conflicting reuse, illegal ownership changes, or distinct events sharing the same `(received_ms,sequence)` invalidate the entire snapshot.

`fixtures/queries.jsonl` contains independent requests with `request_id`, `market`, `as_of_ms`, `action` (`buy` or `sell`), and `lots` (integer 1..10^9). `as_of_ms` is inclusive: apply all events received no later than that millisecond, including every sequence at that time. A buy executes against asks from cheapest to most expensive; a sell executes against bids from highest to lowest. Multiple quotes at one price contribute cumulative lots. The market's quoted supply does not change when a request is evaluated: estimates do **not** execute orders or affect one another.

## One primary customer problem
Implement `QuoteEngine.quote(request)` in `books/engine.py` and any supporting code and tests. For each valid request, compute the best executable quote for up to the requested lots *as of* the requested time. Return exactly these keys:

`request_id`, `market`, `as_of_ms`, `action`, `requested_lots`, `filled_lots`, `unfilled_lots`, `notional_cents`, `marginal_price_cents`, `price_levels_used`, `status`.

- Fill as many lots as are available, in favorable price order; do not invent liquidity. `status` is `filled` if every requested lot can be filled, otherwise `partial` (including when zero lots are available).
- `notional_cents` is the exact integer sum of `lots_at_price * price_cents` for filled lots only; `marginal_price_cents` is the last price used or `null` if no lots fill; `price_levels_used` counts distinct consumed price levels, not dealer quotes.
- For example, a buy of 5 lots against ask offers of 2 lots at 125 cents and 7 lots at 130 cents fills 5, with notional 640 cents, marginal 130, and two price levels. This is only an illustration, not a fixture answer.

## Observable acceptance criteria
For a known market and well-formed query produce exactly the response above; preserve request order even though queries may reference arbitrary historical times. Output one compact JSON object per query line and no diagnostics on stdout. Repeated request IDs are independent. A query for a nonexistent market returns `{"request_id":"...","status":"invalid","reason":"unknown_market"}`. Malformed JSON, missing/wrong fields, unsupported actions, booleans in numeric slots, negative/out-of-range values, and invalid IDs return `status:"invalid",reason:"invalid_query"`; preserve a valid request ID if present, otherwise `null`. Continue after bad queries. Invalid snapshot data fails before any query results, with a useful stderr error and nonzero exit.

Correctly handle out-of-order update files, repeated event IDs, multiple same-price dealers, price changes with old levels becoming empty, cancellation/reopening, updates at the exact queried millisecond with different sequences, empty books, partial fills, distinct bid/ask depths, independent markets, order-independent estimates, integer arithmetic, and deterministic results regardless of source row or query order.

## Production constraints
A single immutable snapshot can contain **3 million updates**, **250,000 quote IDs**, **100,000 distinct prices**, **200 markets**, and **1.5 million arbitrary historical queries**. A few markets may contain almost all events. Target ~**1.5 GB RAM** and p95 **under 20 ms per estimate after preprocessing**. Replaying all prior events, sorting all live quotes, or traversing every price level for each query is not viable; justify complexity for updates, time travel, and liquidity totals. Scale targets are engineering goals, not fixture benchmarks.

## Deliverable and scope
Implement the missing quote-estimation capability, add focused adversarial tests, and explain the design's correctness and time/space costs. You own the strategy: deterministic, heuristic, LLM-based, or hybrid approaches are permitted if the contract remains exact and performant. In scope: as-of estimates, exact multi-level partial execution totals, query error recovery, and verification. Out of scope: actual trade execution, persistence, order matching, fees, credit limits, a UI, external APIs, live streaming after load, and changing supplied fixture data.

## Setup, baseline, and run commands
Python **3.11+**, standard library only:

```bash
bash scripts/build.sh
bash scripts/test.sh
bash scripts/verify.sh
python3 market_book.py validate --events fixtures/updates.csv --queries fixtures/queries.jsonl
```

After implementation:

```bash
python3 market_book.py quote --events fixtures/updates.csv --queries fixtures/queries.jsonl
```

The existing loader, CLI validation path, and starter tests pass before the exercise. They **do not** implement or exhaustively test quote estimation.

## 60-minute AI-assisted interview instruction
You have **60 minutes** with Claude Code, Codex, ChatGPT, or similar tools. Inspect supplied data and starter code, decide how to handle scale and historical queries, implement incrementally, test adversarial cases, and defend tradeoffs and failure modes in a technical walkthrough. A one-shot happy-path answer is insufficient.
