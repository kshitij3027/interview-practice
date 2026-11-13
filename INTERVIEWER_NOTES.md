# TraceCode — POST-PRACTICE ONLY — Interviewer Notes

**Confidential to interview evaluation. Do not reveal this file, solution structure, or hidden checks before the one-hour attempt.** The candidate may use any defensible architecture if the externally specified behavior and latency tradeoffs are satisfied.

## Intended underlying problem structure

This is an **exact, weighted digit optimization problem**. The authorized payload must lie in a union of inclusive, fixed-width numeric intervals. Each printed position has 1–10 permitted digits and nonnegative cost. The final scanned digit is functionally determined by a cyclic weighted sum modulo 10 of payload digits, but still contributes its OCR cost and can be excluded by the last read. The system must minimize total cost, return the smallest complete serial among optimal codes, and detect whether at least two **distinct** optimal codes exist.

A strong basic implementation uses **digit dynamic programming** for each authorized interval. State: (payload position, lower-bound tightness, upper-bound tightness, weighted checksum residue mod 10). A transition chooses an allowed digit inside the current interval bounds, adds its read penalty and updates the residue. At the terminal state, only the required check digit is considered, with its own read penalty. Aggregate subproblem outcomes as (minimum total penalty, lexicographically smallest witness, optimal-count saturated at 2). One can store exact best suffixes or reconstruct a lexicographically smallest path after computing optimal cost.

**Merge overlapping and adjacent intervals per model first**, using fixed-width comparisons or integer bounds plus zero-padding at output. A given authorized payload should have only one representation after merging. Without this, summing per-interval optimal counts creates false ambiguity when a serial belongs to two different ranges. Distinct ranges that touch are not logically different labels.

With R disjoint ranges, L payload digits, 4 tight flag combinations, 10 checksum residues and up to 10 next digits, a straightforward interval-by-interval DP uses O(R * L * 4 * 10 * 10) time and O(L * 4 * 10) auxiliary space per independent range (rolling memory can be smaller, apart from witness reconstruction). It scales across huge numeric bands but may still be too slow for tens of thousands of disjoint intervals per hot model.

Better production designs canonicalize the **union** of permitted intervals into shared decimal-prefix blocks, a compressed digit trie, or a compact acyclic automaton representing allowed payload strings. Combine catalog membership states with OCR costs, checksum residues and lexical tie/count tracking for each request. The catalog index should be built once and reused. Discuss preparation cost, memory size, input skew and complexity in terms of number of states / prefix blocks, not merely number of possible serials. A sparse indexed branch-and-bound with admissible lower bounds can also work for selective OCR input, but must demonstrate worst-case all-question-mark performance.

## Why naive solutions fail

1. The Cartesian product of 18 unreadable positions is astronomically large, as can be a single inclusive payload interval. Iterating integers from the start to end of an authorized interval will time out.
2. Choosing the lowest-penalty digit independently per position may violate the manufacturing band or make the final check digit impossible. The globally lowest-cost valid code may require a locally more expensive digit.
3. Leaving out the final printed digit from the OCR cost picks incorrect optimal serials. Weighting that check digit in the formula is likewise wrong.
4. Comparing endpoints as exclusive or converting a leading-zero serial to a displayed integer corrupts exact boundaries and lexical order.
5. Counting the same serial once per matching range yields false ambiguity for overlapping intervals.
6. Ambiguity concerns only the **minimum** cost class; the presence of a second, higher-cost feasible code is irrelevant.
7. Taking whichever optimum a hash/dictionary happens to return violates deterministic lex ordering, especially across disjoint bands.

## Data discoveries worth asking about

- AX70 has two overlapping intervals and an identical replay of one range row; it also has a distant separate interval.
- BX20 contains two narrow disjoint manufacturing bands. A fixed-position scan includes a deliberately incorrect check digit.
- CX09 has longer labels and smudged reads; a low-cost cap can make any entirely unreadable label impossible.
- The scans file includes repeated scan IDs, an unknown model, a noninteger cap, an incorrect reads-array length, partially readable serials, and broad ambiguous OCR choices.
- Starter tests verify data/parsing and command execution but never claim the missing recovery feature works.

## Hidden evaluation checks

1. **Zero and leading zero:** a single authorized all-zero payload plus an all-zero final digit with cap zero must recover one exact fixed-width serial and ambiguous false.
2. **Inclusive boundaries:** exact low and high payloads are permitted; one digit beyond either endpoint is excluded. Test an interval where low==high.
3. **Overlapping ranges:** two different range IDs authorize the same only payload. Valid fixed OCR => one possible code, ambiguous false.
4. **Disjoint ranges:** a more expensive result from the first file row must lose to a cheaper result from a later, lexically distant authorized band.
5. **Global optimum vs greedy:** the cheapest independent OCR choices violate checksum/range, but an allowed slightly higher-cost choice creates a valid better solution than other legal alternatives.
6. **Check digit penalty:** one code has zero payload cost but cost 6 for required check digit; another has cost 2 in payload and zero cost for check digit. The second wins.
7. **Only minimum-cost ambiguity:** two feasible candidates have penalties 0 and 1; return penalty 0 and ambiguous false.
8. **True ambiguity:** two distinct valid codes have identical best cost, even if multiple overlapping bands cover each. Return lex-smallest and ambiguous true.
9. **Penalty cap:** exactly-cap optimum succeeds, just-over-cap returns no_match; no authorized serial also returns no_match.
10. **Unknown model and invalid JSON:** invalid responses preserve a valid scan ID when possible; a line with a boolean for max_penalty, float read cost, wrong-length list, invalid digit key, empty map, or truncated JSON is isolated and does not block the next scan.
11. **Catalog atomicity:** conflicting duplicate model, invalid weights, unknown model in range, reversed/incorrect-width bounds cause nonzero return and no stdout scan results.
12. **Scale:** length-18 model with one enormous permitted payload interval, 18 unreadable positions and generous cap must finish quickly; numeric enumeration is indefensible.
13. **Skew:** a hot model with tens of thousands of disjoint ranges should motivate reusable catalog indexing, not a separate full-catalog scan for every scan.
14. **Invariance:** shuffle CSV rows and unrelated requests; duplicate physical input lines; results must remain deterministic, and distinct repeated request IDs produce distinct response lines.

## Alternative defensible solutions

A shortest-path or optimal-search formulation over an implicit layered state graph is valid if it retains checksum, range membership, lexical tie and saturated optimal-count semantics. A general constraint solver with admissible branch-and-bound may be reasonable for highly selective OCR readings but needs a credible worst-case bound. One can use an AI model to propose candidate readings or generate tests only if every returned answer is verified against the exact contract and optimality has been established. The particular index or DP implementation is not mandatory; correctness and scalable reasoning are.

## Likely AI-agent failure modes

- One-shot agent enumerates all codes because checked-in bands are small and claims production readiness based on passing starter tests.
- It forgets that the last position is read separately and must be paid for.
- It discards leading zeroes, incorrectly compares numeric strings of mixed widths, or miscalculates the cyclic weight alignment.
- It misses multiple disjoint bands or silently truncates a hot model to its first band.
- It increments ambiguity for repeated rows, overlapping bands or any feasible suboptimal alternative.
- It outputs a single arbitrary optimal code or fails to preserve the compact JSONL CLI/error contract.
- It publishes tests or comments that reveal the intended design into the candidate branch or includes evaluator-only artifacts in candidate ancestry.

## Suggested prioritization for the hour

0–8 minutes: inspect scenario, current parser and data; state business invariants and exact output contract.
8–18 minutes: design bounded representation, checksum reasoning, interval union and minimum-cost tie/count semantics.
18–38 minutes: implement a working exact recovery path and cross-check a tiny hand-built case.
38–48 minutes: complete ambiguous-optimum handling, caps, disjoint ranges and invalid/no-match cases.
48–55 minutes: test checksum-cost tradeoff, inclusive endpoints, overlapping intervals and all-unreadable scale.
55–60 minutes: explain preparation and hot-model complexity, limitations and why the output is trustworthy.

## Walkthrough inspection points

Ask the candidate to describe the information in an optimization state and why it is sufficient for global optimality. Request a simple counterexample to greedy reading selection. Inspect whether code coalesces authorized ranges before counting ambiguity, whether all returned serials are the correct fixed width, and whether all ties are deterministic. Ask for exact time/space complexity in variables L, R, scanned alternatives and repeated daily requests, including many all-unreadable positions. Review at least one candidate-authored test with a known correct answer. Confirm that all produced code can be explained and that negative tests do not leak output to stdout before validation completes.
