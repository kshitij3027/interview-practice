# ScanLedger wire contract

The repair runner must return exact data types and keys. All offsets refer to the original observed and planned sequences, starting at zero.

## Repairs
Each repair represents one nonmatching alignment step at the pair of currently unconsumed positions `(i,j)`.

- `missing`: consume planned checkpoint `route.sequence[j]` but no scan; fields: `type`, `observed_offset: i`, `expected_offset: j`, `expected_code`.
- `unexpected`: consume observed scan `scans[i]` but no planned checkpoint; fields: `type`, `observed_offset: i`, `expected_offset: j`, `observed_code`.
- `incorrect`: consume both *different* checkpoint codes; fields: `type`, `observed_offset: i`, `expected_offset: j`, `observed_code`, `expected_code`.
- `match`: consume both *equal* checkpoint codes and emit no repair.

Choose the complete alignment with fewest nonmatches, then fewest `incorrect` steps, then lexicographically smallest **full** step-type string with `match < missing < unexpected < incorrect`. Repeated codes are separate positions. Report repairs in traversal order.

## JSONL responses
The CLI outputs one object per request, in request order, and no diagnostics on stdout.

Successful: `{"request_id":"q","status":"reconciled","route_id":"R-METRO-7","repair_count":1,"repairs":[{"type":"missing","observed_offset":2,"expected_offset":2,"expected_code":"LOCKER_12"}]}`

Beyond budget: `{"request_id":"q","status":"unrepairable","route_id":"R-METRO-7","max_repairs":1}`

Valid request naming a nonexistent route: `{"request_id":"q","status":"invalid","reason":"unknown_route"}`

Malformed JSON/fields: `{"request_id":null,"status":"invalid","reason":"invalid_query"}`. Preserve a supplied nonempty string request ID if possible, even when other fields are invalid. Invalid queries cannot stop later lines. Invalid route catalog data **must** stop loading with stderr output and nonzero exit.

A zero-repair success has `repair_count:0` and an empty `repairs` array. Any repaired result must consume the entire planned route and the entire original scan tape. The `max_repairs` threshold is inclusive.
