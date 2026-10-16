# POST-PRACTICE ONLY — Interviewer Notes

## Intended solution
This is exact, bounded sequence alignment. State (i,j) identifies consumed observed and expected checkpoints. Equal-code match costs (0 repairs,0 substitutions); missing and unexpected steps cost (1,0); replacing differing codes costs (1,1). Optimize the repair/substitution pair and finally the full step sequence under match < missing < unexpected < incorrect.

The key production constraint is k<=16 repairs. Successful alignments stay within |i-j|<=k; narrow-band dynamic programming targets O((n+m)k) time. Suffix-optimal costs plus forward lexicographic selection give deterministic traceback. Compact traceback or checkpointing can meet a 256 MB budget. A dense O(nm) table fails on 200k scans; the 250 ms target needs benchmarking.

## Test cases and subtle traps
Swapped codes favor a missing+match+unexpected plan over two replacements. Expected [AA,AA] vs observed [AA] chooses match then missing at (1,1). Check empty scans, trailing corrections, duplicate positions, original offsets, equality at budget limits, unknown scan labels, repeated route visits, and long impossible tapes. Check malformed JSON between good requests, duplicate catalog deliveries, conflicting route IDs and boolean budgets.

## Alternatives and failure modes
Native implementations, banded graph search and divide-and-conquer reconstruction can be defensible. Naive two-pointer corrections, approximate sequence-matching utilities, an unconstrained LLM, and memory-heavy all-pairs tables are not exact/scalable. A simple exhaustive oracle for short tapes is useful evidence.

## Walkthrough priorities
Minutes 0–8: contract and data. 8–22: optimal bounded cost. 22–40: canonical script. 40–52: tests. 52–60: benchmark, proof and tradeoffs. Evaluate problem decomposition, failure demonstrations, explanation of AI use, and resource estimates.
