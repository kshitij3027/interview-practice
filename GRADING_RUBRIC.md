# POST-PRACTICE ONLY — Grading Rubric (100 points)

Decomposition and domain invariants: 15
Core correctness: 20
Approach and data structures: 15
Complexity and scalability: 14
Edge-case correctness: 12
Verification and tests: 10
Code and interfaces: 8
Walkthrough and tradeoffs: 6
Total: 100

For excellent decomposition, the candidate must distinguish wall-clock from business time. Correct solutions produce exact deadlines, elapsed seconds, remaining seconds, and breached status. Strong technical approaches preprocess immutable regional calendars and avoid repeated full scans. The candidate should document memory requirements and tests for boundaries, overlaps, offsets, replay, malformed inputs, and unreachable deadlines.

A solution handling only straightforward fixture examples should receive no more than 55 points. Repeated whole-dataset scanning should receive no more than 58 points. Double-counting overlapping availability should receive no more than 60 points. Code with correct small examples but no credible approach to stated scale should receive no more than 65 points.
