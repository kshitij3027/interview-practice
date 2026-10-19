# POST-PRACTICE ONLY — Interviewer Notes

## Intended underlying structure
Immutable regional coverage intervals with overlapping availability and exclusions, cumulative business-time totals, per-ticket exclusions, and ranked deadline summaries.

## Strong implementation
Normalize RFC3339 timestamps to integer UTC seconds. Union overlapping and adjacent regional coverage windows. Union regional blackout windows, then subtract them once from covered time. Build covered-second cumulative totals, supporting a binary search for covered seconds at a timestamp and an inverse query for the earliest timestamp reaching a positive covered-time target.

For a ticket, transform pause endpoints into region-level covered-time coordinates, clip before opening, merge overlapping pauses, then subtract their cumulative covered duration from the ticket clock. Find its deadline using the allowance and transformed exclusions. A zero allowance is due immediately at opening. The finite calendar can make a deadline unreachable. Store ticket deadlines once and rank reachable ones by deadline and ticket ID for overdue queries.

## Complexity
Let C, B, P, T be numbers of coverage intervals, closures, pauses and tickets. Preprocessing is O((C+B)log(C+B)+P log P+P log C+T log T). Memory is O(C+B+P+T). Individual ticket queries cost O(log C_region+log P_ticket), and overdue top-k queries cost O(log T+k).

## Failure modes
Summing raw overlapping windows, subtracting pauses or closures twice, rounding at minute boundaries, ignoring time offsets, inclusive end errors, and per-query full scans all break correctness or scaling.

## Checks and walkthrough
Test repeated rows, shifted time offsets, touching windows, zero allowance, infinite pauses, missing records, malformed requests, and stable overdue ordering. Ask the candidate to trace the opening 30-second case. Prioritize coverage first, ticket pauses second, query recovery and measured performance last. Alternatives may cache ticket-specific effective intervals at a higher memory cost.
