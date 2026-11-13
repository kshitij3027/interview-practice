# TraceCode — HARD 60-Minute AI-Assisted Customer Interview

## Customer and business context

A medical-device distributor receives damaged equipment labels. An upstream OCR scanner reports plausible digits and a penalty for each reading rather than one reliable serial number. The distributor also knows which manufacturing number ranges were actually issued for each product model and how the printed check digit was calculated. Guessing a false serial might link a real medical device to the wrong warranty or recall history.

Build **one trustworthy serial-label recovery capability** for an immutable manufacturer catalog and independent scans. You own the technical strategy; deterministic, heuristic, AI-assisted, or hybrid solutions are welcome as long as the exact observable contract is satisfied. No external SDK, API key, paid service, or image processing is necessary.

## Data supplied

- **fixtures/models.csv** contains model_id, length, weights. Length is the number of printed decimal digits, including the final check digit, and is between 8 and 18. Weights is a sequence of one to eight digits from 1 through 9, repeated left to right in the checksum calculation.
- **fixtures/ranges.csv** contains range_id, model_id, first_payload, last_payload. Each row authorizes every payload between the endpoints, **inclusive**. Payloads consist of the first length-1 printed digits, with leading zeroes preserved. Two intervals for the same model may overlap, touch, or be disjoint. Overlap must not count a serial twice.
- **fixtures/scans.jsonl** contains one independent scan per physical line, including invalid and impossible scans. Repeated scan_id values are independent requests, not an idempotency key.
- **tracecode/catalog.py**, **tracecode/contracts.py**, **tracecode/cli.py**, and **tracecode.py** provide working snapshot validation, request parsing, and a CLI. The requested capability is unfinished in **tracecode/engine.py**.
- **tests/** and **scripts/** provide a green baseline; the starter tests do not fully implement or verify customer acceptance.

CSV files contain exactly their documented headers, in any order. Model and range IDs use case-sensitive ASCII letters, digits, underscores or hyphens, length 1 to 48; scan IDs may have length 1 to 128. Replayed identical declarations of the same ID are harmless, but conflicting declarations invalidate the **entire catalog before any scan output**. A range for an unknown model, a reversed interval, or an incorrectly sized numeric endpoint invalidates the whole catalog. A model may have no authorized ranges.

## Printed serial and OCR semantics

For a model of total printed length L, a candidate serial contains an L-1 digit payload followed by one check digit. Let payload[i] denote the numeric digit at position i, with i=0 at the leftmost position. Let weights repeat from the left.

    check_digit = (sum(payload[i] * weights[i % len(weights)]
                       for i in 0..L-2)) % 10

Only payload values within at least one authorized manufacturing interval for that model can be chosen. Each manufacturing interval refers to the payload, **not** the trailing check digit. Leading zeros are meaningful throughout.

Each valid scan request contains **scan_id**, **model_id**, **max_penalty**, and **reads**. The maximum penalty must be an actual JSON integer 0 through 1000, not a float, boolean, or numeric string. The reads array contains exactly L entries, one for each printed digit, including the check digit.

Each read is either **"?"**, meaning any digit 0 through 9 is possible with penalty 3, or a nonempty JSON object mapping individual digit-string keys ("0" through "9") to integer reading penalties 0 through 9. Only its listed digits are allowed. The total reading penalty is the **sum across every printed digit**, including the final check digit. No other OCR substitutions are permitted. Extra JSON object fields on the request are ignored.

For illustration, a valid AX70 request can have a reads array of length 12, with explicit objects for legible digits and question marks for missing digits:

    {"scan_id":"example","model_id":"AX70","max_penalty":15,
     "reads":["?",{"0":0,"8":2},"?","?","?","?","?","?","?","?","?","?"]}

## Primary customer request

Implement **SerialRecovery.recover(scan)**, plus any justified catalog preparation. Consider **all distinct valid full serials** satisfying the model-specific manufacturing ranges, allowed OCR choices, and printed check digit. Discard serials whose total reading penalty exceeds max_penalty.

If any admissible serial remains, minimize total penalty. Among serials with the same minimum penalty, return the **lexicographically smallest full serial**. Also report whether **two or more distinct serials attain that exact minimum penalty**; a more expensive feasible serial does not make the optimum ambiguous. Different overlapping range records that refer to the same full serial do not make it ambiguous.

Successful result shape, with illustrative values only:

    {"scan_id":"example","status":"ok","serial":"000000000000","penalty":3,"ambiguous":true}

When no candidate is admissible, including when the best candidate exceeds the cap:

    {"scan_id":"example","status":"no_match","serial":null,"penalty":null,"ambiguous":false}

The CLI emits one **compact UTF-8 JSON object per physical input line**, in original order, even if IDs repeat. Malformed scan lines produce an isolated invalid response with reason **invalid_scan** and a valid scan ID if recoverable, otherwise null. A syntactically valid but undeclared model produces reason **unknown_model**. Bad scan lines do not poison later lines. Bad catalogs instead fail atomically, nonzero with a useful stderr diagnostic and no scan result lines. Do not send progress messages to stdout.

## Observable acceptance criteria

- Respect payload length, leading zeroes, model boundaries, and both **inclusive** range endpoints.
- Use all allowed OCR alternatives, not simply the cheapest independent digit at every position; validate the whole serial against both authorization and check digit.
- Include the final digit reading penalty. An impossible or unlisted check digit must reject the serial, even if its payload was authorized.
- Find the **globally least** total penalty, then apply deterministic case-sensitive lexicographic choice of full serial. Report ambiguity only when two or more distinct minimum-cost serials exist.
- Handle overlapping manufacturing bands, adjacent bands, multiple disjoint bands, one-number bands, all-unreadable scans, and no-solution scans.
- A total penalty exactly equal to max_penalty is allowed; one greater must not be returned.
- Validate every scan field and its JSON type; reject empty digit-choice objects, bad digit keys, negative or noninteger costs, wrong read-array lengths and invalid IDs.
- Catalog row order, repeated identical rows, unrelated query order and repeated scan IDs must not affect the individual answer. One malformed scan must not stop valid later scans.

## Constraints and engineering tradeoffs

The checked-in data is deliberately small. Production may have **200,000 device models, 1.5 million manufacturing intervals, and 100,000 independent OCR scans per day**. A popular model may have **tens of thousands of disjoint authorized intervals**; serials may be 18 digits long, and some scans allow all ten digits at many positions. Aim for **512 MB working memory** and **p95 under 75 ms for typical requests after one catalog load** on one worker. These are design targets, not fixture benchmarks.

Do not enumerate every decimal serial or every combination of allowed OCR digits. A fresh full-catalog scan for each request will not handle skew toward popular models. Be prepared to explain how catalog preparation helps, how you bound work on unreadable scans and busy models, what preprocessing costs, and how you would check worst-case latency and memory. You may choose your own indexes, search strategies, heuristics, or models, but observable correctness is exact.

## Deliverable, setup and scope

Deliver the recovery implementation, focused tests you derive, and a concise explanation of assumptions, correctness, scalability, deterministic ordering, and failure modes. You may refactor the starter, provided the CLI, validation, error and output contracts remain intact. The customer does **not** ask for image ingestion, OCR training, a UI, API integration, databases, patient records, or live catalogue changes.

Use **Python 3.11+**, standard library only. Run these commands from the branch root:

    bash scripts/build.sh
    bash scripts/test.sh
    bash scripts/verify.sh
    python3 tracecode.py check --models fixtures/models.csv --ranges fixtures/ranges.csv

After implementing the requested feature, run:

    python3 tracecode.py recover --models fixtures/models.csv --ranges fixtures/ranges.csv --scans fixtures/scans.jsonl

The starter deliberately returns **not_implemented** on valid scans. Passing starter tests alone does not fulfill the feature request.

## The 60-minute AI-assisted interview

**You have 60 minutes, and using AI is explicitly encouraged.** Use Claude Code, Codex, ChatGPT, or similar assistants the way you would on a real customer escalation. First inspect the data, understand the goal, and clarify assumptions. Then choose an approach, implement incrementally, verify outputs with adversarial examples, and prepare to defend its correctness, time/space complexity, tradeoffs, and failure modes. You should be able to explain what your AI-generated code actually does.
