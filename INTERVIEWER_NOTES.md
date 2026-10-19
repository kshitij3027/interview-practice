# POST-PRACTICE ONLY — SatLink interviewer notes

This file belongs only on the separate evaluator branch.

## Intended solution structure
The problem concerns sparse byte intervals, overlap verification, sorted coverage runs, and indexed range reads. Never allocate by the manifest size: an asset can claim 10^12 bytes with almost no captures.

Group fragments by asset, sort by offset, and merge adjacent or overlapping covered runs. On overlap, compare every shared byte, record the smallest absolute conflicting offset across the entire asset, and add only newly exposed bytes. Count the lengths of nonoverlapping runs. Find the first missing position from the first run (or 0 when none begins at 0). Hash a fully covered and conflict-free asset once in offset order; compare against expected SHA-256 when supplied. Index run starts for quick predecessor search on each read. Missing reports the first absent byte inside the requested range. Empty reads are available on noncorrupt assets. Alternative designs include balanced interval maps, chunked byte buffers, and disk-backed storage.

## Complexity
With F fragments and B total delivered bytes, preprocessing can be O(F log F + B); unique bytes U require O(U) hashing at most once; reads O(log R + K) for R covered runs and at most K=4096 output bytes. Working memory O(F + U + R), including substantial Python object overhead. Measure the 1.5 GB target.

## Failure modes and hidden checks
Naive dense allocation, duplicate-counted coverage, last-write-wins contradiction handling, returning the first encountered rather than minimum-position conflict, repeated immutable-byte concatenation, linear scan per query, hashing base64 instead of raw ordered bytes, or leaking reads from checksum mismatches.

Check shuffled fragments, nested and repeated overlaps, duplicate and conflicting capture IDs, sparse 10^12-sized export, zero-byte export and empty reads, one-byte gaps, binary payloads, malformed requests followed by valid records, and high query volume.

## Fixture oracle and 60-minute plan
A-STRIP is complete with 12 bytes; B-HOLE partial with 10 covered and first missing 7; C-CONFLICT corrupt at 3 with 7 covered; D-SHA checksum mismatch; E-EMPTY complete and empty; F-SPARSE partial with 2 covered and first missing 1.

Minutes 0–8 inspect, 8–35 build coverage/conflict logic, 35–45 checksum/reads, 45–55 test edge cases, 55–60 explain data structures, complexity, tradeoffs and AI-assisted versus deterministic choices.