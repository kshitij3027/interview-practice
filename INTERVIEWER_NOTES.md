# POST-PRACTICE ONLY — Interviewer Notes

The core challenge is exact, bounded sequence alignment. Each state tracks consumed observed and expected positions. Match equal codes for zero cost; insert missing, remove unexpected, or replace incorrect codes for one repair. Optimize total repairs, then substitutions, then the full step sequence.

A strong solution exploits the maximum budget k=16: successful paths stay within a narrow band around equal consumed positions. Banded dynamic programming targets O((n+m)k) time; compact suffix-cost storage supports canonical traceback. Dense O(nm) tables and local greedy correction fail at 200k tokens.

Test swaps, repeated labels, empty inputs, trailing corrections, tie ordering, budget boundaries, malformed rows, duplicate IDs, and large impossible tapes. Inspect time/memory justification, correctness proof, AI-tool verification, and the 60-minute prioritization.