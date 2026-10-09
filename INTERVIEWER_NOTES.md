# ClaimSignal — Interviewer Notes

**POST-PRACTICE ONLY — EVALUATOR MATERIAL. Never show before the 60-minute attempt.**

## Underlying technical structure

This is multi-pattern substring detection plus cardinality-constrained maximum-weight non-overlapping interval selection with deterministic multi-level tie-breaking. It is not an LLM prompt or a simple substring loop. Search and global selection are separable: source text is ASCII, so ASCII lowercasing preserves character offsets; catalog normalization is case-insensitive only, without collapsing whitespace or punctuation.

**Strong approach:** preprocess active catalog phrases into a reusable shared search representation (e.g., Aho–Corasick automaton, or another proven multi-pattern index). A terminal may represent multiple rules with the same case-insensitive phrase. Scan the note once, enumerate eligible occurrences and apply channel plus whole-token boundary checks using the *original* characters. For each accepted occurrence, retain start, end, rule metadata, weighted score and coverage; do not deduplicate distinct rule IDs sharing a phrase. Sort occurrences by end (with reproducible secondary keys). For each occurrence i, find the rightmost predecessor whose end <= its start via binary search. Use capacity-aware weighted interval selection over at most k<=8 annotations. Each state compares complete outcomes by (higher total score, higher coverage, fewer findings, lexicographically smaller sorted triples). Maintain a compact deterministic backpointer or a small tuple of up to k entries for tie decisions. Output findings sorted by `(start,end,rule_id)` and obtain text by slicing the original note.

If one phrase occurs at the same span for several rules, each is a distinct competing candidate; at most one may be selected due to overlap. A compact terminal mapping phrase -> active rule variants is useful, but must not erase channel-dependent or score-dependent choices.

## Complexity and production posture

Let P be total catalog phrase length, n note characters, h total eligible occurrences and k<=8. A multi-pattern preprocessor can achieve O(P * alphabet transition factor) preprocessing and O(n+h) matching in the usual representation; memory O(P + rule mappings), subject to the chosen transition representation. Sorting findings O(h log h), predecessors O(h log h), bounded interval selection O(kh) transitions plus tie representation costs. Total per note roughly O(n + h log h + kh). Naively storing full tuples on every DP state adds O(k) each, making O(k^2 h) worst case, tolerable for k<=8 on normal inputs but worth exposing for dense notes. An index based on Python object dictionaries may be memory-heavy at 150k phrases; sparse transition structures, array/trie layouts or grouping by normalized phrase are defensible tradeoffs. Extremely dense output makes O(h) itself a lower bound if every eligible occurrence must be considered; discuss pruning/dominance and memory pressure before claiming unconditional 100ms.

A smaller-data strategy using a dictionary of first characters with direct substring confirmation may be an acceptable *incremental* bridge, but cannot claim the 150k-rule target without measured bounds. Aho–Corasick is one strong option, not a required architecture: any approach with correctness and credible asymptotics scores fully. LLM tagging is not necessary; if proposed, output must be verified against the exact contract and ties and latency need defense.

## Why naive/agent approaches fail

- `for rule in rules: text.find(rule.phrase)` rescans each note 150k times, and `find` with index advanced by pattern length misses overlapping occurrences.
- Greedy longest phrase, highest weight, highest score, or earliest occurrence ignores the global combination and k budget. Picking all hits and trimming afterward is also wrong.
- Using a Python `set` for phrases erases distinct rule IDs at identical spans; using maps keyed on phrase loses per-channel restrictions.
- Simple `str.lower()` is safe here only because both inputs are ASCII; broad Unicode assumptions and whitespace normalization alter observable offsets.
- Using regex `\b` without checking precise ASCII alphanumeric boundaries can surprise on underscores and nonstandard strings; the specified boundary is not the regex language default.
- Treating each character interval as closed makes adjacency conflict; `[start,end)` semantics permit it.
- Ranking individual matches rather than complete sets mishandles secondary tie breaks, especially fewest findings and lexicographic ordered tuples.
- Boolean `max_findings=True` passes `isinstance(True,int)`; starter correctly rejects it. Service must not silently reinterpret malformed requests.
- Query filename order and repeated case IDs may be corrupted by caching results keyed on case_id.
- Printing debug messages to stdout corrupts JSONL parsing.

## Hidden check plan

1. Same phrase under two distinct rules and overlapping channel applicability; winner differs across channels, with exact-span tie resolved by rule_id.
2. Exact catalog replay row accepted once; same ID with even a small raw-field change rejected, including reordering channel tokens.
3. `leak` in `leaking` excluded, but in `leak-leak` both occurrences accepted. End-of-note and beginning-of-note boundary behavior.
4. Phrase `roof damage` conflicts with `roof` and `damage`; chosen set must maximize summed weighted coverage, not longest phrase.
5. With max_findings=1 versus 2, optimal selection can change completely; cannot compute unconstrained set then truncate.
6. Two distinct sets equal score but different coverage; choose more coverage. Then tie same coverage but different count; choose fewer. Then tie all numeric fields; use ascending tuple-sequence comparison.
7. Offset preservation for uppercase source text and punctuation; selected `text` is exactly `case.text[start:end]`.
8. Repeated occurrence of the same phrase; duplicate IDs on distinct request lines yield independent outputs. Shuffle catalog rows repeatedly; outcomes unchanged.
9. Empty note, zero eligible rules in channel, all inactive phrases, max_findings > available matches, and missing requested code (never fabricate).
10. Invalid JSON followed by valid line; null/nonobject records, boolean/numeric-string limits, non-ASCII request text, invalid channel, missing fields, empty case ID.
11. Dense adversarial catalog with many nested phrases and same-span rule variants; assess memory, correctness and latency. 150k unrelated phrases against a short note must not require 150k independent scans.
12. Compare candidate on dozens of small random inputs against exhaustive subset enumeration of nonoverlapping candidates with max_findings<=3; use random selection rule IDs and channels.

## Discoveries expected from fixtures

`R07` is delivered twice identically; `R02` and `R15` share exact phrase/weight but are distinct rules; `R01` and `R17` share phrase but represent distinct competing IDs. `R16` is inactive despite a very high weight. Email/phone/chat eligibility differs. C04 has `leak-leak` followed by `leaking`, demonstrating exact boundaries. C06 tests case-insensitive spans and a one-finding budget. C09/C10 and the malformed JSON line are query-level invalids; C12 afterwards is still valid. C01 contains several overlapping opportunities.

## Expected 60-minute prioritization

Minutes 0–8: inspect fixtures, articulate semantics and complexity risks. Minutes 8–20: build a correct hit emitter with channel/boundary checks and a small corpus test. Minutes 20–40: globally optimal selection with cardinality and exact ties. Minutes 40–50: integrate CLI output/invalid line continuation and preserve existing validation. Minutes 50–60: adversarial tests, incremental scale improvements, discussion of time/memory and AI-agent oversights. A candidate who clearly states a scalable design but only partly implements it can still score above a fully working brute-force demo, subject to the rubric ceilings.

## Interviewer walkthrough

Ask how duplicate phrases are represented, how match boundaries are checked without moving offsets, how predecessor compatibility handles adjacency, what each selection state represents, why its comparison is a total order, and whether the k dimension applies during optimization or only afterward. Change k and channel on the same text; insert a competing rule of the same score; reorder the CSV; use a second case with an identical case ID but different text; show worst-case memory for dense hits. Inspect additional tests, not just green starter tests. Ask the candidate to point out an AI-generated suggestion they rejected or modified and explain why.
