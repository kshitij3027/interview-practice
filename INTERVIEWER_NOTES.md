# QuoteScope Interviewer Notes — POST-PRACTICE ONLY

## Intended underlying problem structure
This is historical replacement-event replay with exact price-ordered partial liquidity aggregation. Updates are SETs of per-quote quantity and price. Quotes belong to a fixed market and side, but prices move. Valid requests are read-only snapshots at arbitrary inclusive millisecond timestamps.

## Strong solution
A credible high-scale design sorts queries by as-of time while retaining original output indexes. Sweep deduplicated events sorted by (received_ms, sequence), applying all events at the queried millisecond. Maintain each quote ID's current price and lots, and per-market/side compressed price ladders in favorable order (ascending asks, descending bids). A cumulative indexed structure tracks lots, price-times-lots, and nonempty price-level counts; when an update arrives, remove the previous quote contribution and add its new contribution. A query locates the marginal fill price, derives total price in cents, and counts distinct occupied levels without scanning them all.

Good implementations use Fenwick trees, segment trees, or augmented ordered trees. Sorting is O(E log E + Q log Q); with P price coordinates, updates and queries are each O(log P), memory O(E + Q + P + quote IDs). One may instead build persistent historical snapshots for online random-time queries, but must discuss memory. A straightforward per-query replay costs O(EQ); sorting or scanning all price levels per query fails the given scale.

## Traps and hidden checks
1. Identical replay of update u08 must count once; conflicting reuse fails the snapshot.
2. Input CSV is deliberately not chronological: BOLTS historical updates follow newer CHIPS rows.
3. Exact as-of timestamp includes ALL updates at that millisecond; sequence resolves intra-millisecond changes.
4. A2 and A3 are distinct dealers at the same 145-cent ask price; they count as one consumed price level.
5. A1 moves price 150 to 140; the previous level must lose its lots.
6. A1 and A2 are cancelled at zero lots and later reopened; no ghost liquidity.
7. Buy consumes lowest asks; sell consumes highest bids; estimates do not mutate book state.
8. Before the first CHIPS update, no fill is possible and marginal price is null.
9. Markets are independent; even identical price numbers do not combine.
10. Queries and request IDs may repeat or arrive out of chronological order; output retains input order.
11. Invalid JSON and boolean numbers are invalid per-record, while snapshot errors fail before any output.
12. Use integer arithmetic for cents and very large volumes; avoid floats.
13. When an occupied level becomes empty, update both its quantity and active-level count.

## Data discovery
The fixture has 18 CSV rows but only 17 distinct updates, two markets, multiple 145-cent ask dealers, price changes, cancellations, reopens, and 13 query records (3 malformed queries).

## Recommended prioritization and walkthrough
Minutes 0–10: inspect data and state invariants. Minutes 10–25: implement historical ordering and per-quote replacement. Minutes 25–45: efficient cumulative depth and partial-fill calculation. Minutes 45–55: adversarial and small-reference tests. Minutes 55–60: demonstrate execution and defend complexity.

Ask the candidate to walk through buy 7 lots at 1000ms and sell 10 at 1200ms; inspect stale-price removal, price-level occupancy, inclusive timestamps and input-order preservation. Common AI-agent failures include per-query sorting, scanning all dealer quotes behind helper functions, old price retention, incorrect prefix boundaries and passing only the provided baseline tests. Accept alternate designs that demonstrate exact results and credible scale behavior.
