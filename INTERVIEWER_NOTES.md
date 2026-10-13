# POST-PRACTICE ONLY — Interviewer Notes

Intended structure: tenant+normalized-query rule mapping; validate article IDs before preview; preserve ordered pins but treat boost/hide ordering as irrelevant. Filter tenant/category/publication first, then hide, include eligible zero-score pins, boost only positive textual matches by 5, rank remaining by score descending and ID ascending, and limit last. A simple correct approach takes O(n log n + k) time and O(n+k) memory for n articles and k<=8 decisions. Indexes or bounded top-k can reduce production latency.

Publication: retain server-owned immutable preview intent and observed tenant revision. Check already-successful tenant/key/intent replays before staleness; reject reused key with different intent. New writes require unchanged tenant revision; change tenant/rule revisions exactly once, no-op neither.

Hidden checks: Unicode 'ＬＯＧＩＮ' normalizes to login; oc-105 is eligible but score-zero, excluded by account filter; oc-107 archived and hc-201 cross-tenant are invalid. Test duplicate IDs, three pins, nine actions, limit=1, hide totals, boost-zero, tie by ID, reordered boosts (no-op), reversed pins (change), stale preview after note edit, lost-response replay after later edits, and an obsolete browser preview response.

Naive/AI failures: curating after pagination loses pins; raw query keys split equivalent intents; client-authoritative ranks bypass validation; premature staleness check breaks successful retries; unguarded fetches overwrite new selections; per-decision revisions inflate updates.

Alternative: signed preview token instead of server preview map, if tamper-resistant and revision-bound. Inspect search, store, HTTP and browser integration. Prioritize 0–25 minutes domain, 25–40 preview/retries, 40–52 UI, 52–60 tests and walkthrough.
