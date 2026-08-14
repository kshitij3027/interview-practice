# Phase 6 — Verification, hardening and documentation

The feature is functionally complete after Phase 5. Phase 6 is about being able to *demonstrate*
that it is correct: closing the gaps the earlier phases knowingly left, fixing a real fragility in
the e2e suite, and writing down the semantics the README requires to be documented.

Files touched:

| File | Change |
| --- | --- |
| `e2e/funnel.e2e.js` | per-test isolation; 3 new tests |
| `test/routes.test.js` | 1 new test (delay ceiling honoured end to end) |
| `NOTES.md` | **new** — funnel semantics, decisions, how to run everything |
| `README.md` | untouched — it is the exercise spec, not solution documentation |

No changes to `src/` or `web/` are planned. If Phase 6 finds a defect that requires one, that is a
finding to report, not a silent edit.

---

## 1. The e2e suite's real fragility: shared state

The current suite creates one browser, one page and one API process in `before`, and every test
inherits whatever the previous test left behind. Concretely, `a slow older report…` excludes
`u-102` and every later test depends on the dataset then being at revision 2. That means:

- tests cannot be run individually (`--test-name-pattern` breaks them),
- a failure in test 3 cascades into misleading failures in 4–7,
- reordering or adding a test silently changes the fixtures the others see.

Two of those already bit during Phase 5: when the restart test failed, tests after it failed too,
and the 30-second timeout in one mutation run was cascade damage rather than a real signal.

**Fix:** restart the API and reload the page before each test, so every test starts from a fresh
revision 1 with no exclusions.

```js
beforeEach(async () => {
  await stopApi();
  await startApi();                       // fresh DataStore: revision 1, nothing excluded
  await page.goto(`http://localhost:${WEB_PORT}/`);
  await page.waitForSelector('table.report');
});
```

Cost is roughly 200ms per test — acceptable, and it buys independence.

**This is not an infrastructure-only change, and pretending otherwise would break the suite.**
Several current tests bake in state their predecessors created, so isolation forces their setup
*and* their expected values to change:

| Test | Hidden dependency today | Explicit setup after isolation |
| --- | --- | --- |
| segment race | expects `revision 2` and `treatment 1/1/1/1`, i.e. `u-102` already excluded by the previous test | exclude `u-102` itself, wait for the report to settle, then run the race; or run the race at revision 1 and expect `treatment 2/2/2/2` |
| server restart | assumes the client already knows `revision 2`, so the reset to 1 is a regression | exclude a user first to reach revision 2, let the report settle, *then* restart the API |
| exclusion validation | relies on `u-100` being present and included | fresh state guarantees it; no change needed beyond the reset |
| failure | uses whatever report happened to be on screen as "last known-good" | run a successful report first, capture its rows, then stop the API |

So each test becomes: **arrange** (establish its own revision and exclusions) → **act** → **assert**
against values derived from its own arrangement, never from run order.

Once rewritten, the Phase 5 mutation checks are re-run to confirm the race tests still fail with
the staleness guards disabled — a rewrite is exactly the kind of change that can quietly turn a
sharp test blunt again.

---

## 2. Coverage gaps to close

Each of these is a path that exists in the shipped code but is currently unverified.

### 2.1 Zero denominators reach the UI as `—` (AC 7, e2e)

`rate()` returning `null` is unit-tested, and `formatRate` renders `—`, but no test proves the two
meet. Exclude every user in a variant, run the report, and assert the row shows `0` counts with
`—` rates rather than `NaN%`, `null%` or `0.0%`.

Reaching it: exclude all four `control` users, then report on `all`. Control then has
`eligible: 0`, so all three rates are `null`.

### 2.2 A single stale response triggers exactly one refetch (AC 11, e2e)

Phase 5's race tests exercise `discard`. The `refetch` branch — response older than the known
revision, on the *newest* request — is only covered by unit tests of `classifyReport`, never
end-to-end.

Reaching it needs both halves of the condition at once, which is easy to get wrong: mutating the
dataset with a direct `fetch` from the page keeps `latestRequestId` unchanged, but it *also* means
the app never calls `applyRevision`, so `knownRevision` stays at 1 and the response classifies as
`apply`, not `refetch`. The known revision has to advance **without** issuing a funnel request.

`refresh()` does exactly that: it calls `applyRevision` from the overview/users responses and does
not call `loadReport`. So the sequence is:

1. delay 5000, click **Run report** — request 1 computes at revision 1 and then sleeps;
2. drop the delay to 0, so the eventual refetch is fast;
3. mutate the dataset with a direct `fetch` PATCH from the page — revision becomes 2, no UI
   request is issued and `latestRequestId` stays 1;
4. click **Refresh** — `refresh()` advances `knownRevision` to 2 while leaving `latestRequestId` at 1;
5. request 1's response lands: newest request ✓, segment matches ✓, `revision 1 < 2` → `refetch`.

Assert the report ends at revision 2 with the mutated user gone, no error banner, and the notice
area empty — that last one distinguishes `refetch` from the `resyncRevision` path, which would
have written a restart message.

### 2.3 The `delay_ms` ceiling is honoured end to end (AC 10, routes)

`parseDelayMs('99999') === 5000` is unit-tested and `delay_ms=120` is honoured, but nothing proves
the *clamp* reaches the transport — a route that passed the raw value through would still pass both
tests. Assert `?delay_ms=99999` returns in comfortably under 10s (it would otherwise wait 99s),
with a generous bound so the test is not timing-flaky.

### 2.4 Revision monotonicity during normal operation (AC 9, e2e)

`nextRevision` is unit-tested in isolation. Worth one end-to-end assertion that the *displayed*
revision never decreases across a sequence of overview/users/exclusion/funnel responses.

**Scope this to non-restart flow, or the test fights the implementation.** `resyncRevision`
deliberately lowers the revision when an authoritative overview proves the API restarted, and that
is correct: the README documents that restarting resets exclusions, so a client pinned to a
revision the server no longer has would wedge. A blanket "never decreases" assertion would
therefore be asserting a rule the design intentionally does not have.

So the test covers a normal session only — refresh, exclude, include, re-run the report, switch
segments, with no restart — and asserts the displayed revision is non-decreasing throughout. The
restart exception stays covered by its own test (§1), which asserts the opposite behaviour on
purpose, and `NOTES.md` records that the monotonic rule holds for responses and is overridden only
by an authoritative reset.

---

## 3. `NOTES.md`

AC 4 requires the duplicate-resolution rule to be **documented**, and right now it lives only in a
code comment. A reader should not have to open `src/funnel.js` to learn the semantics they are
being asked to evaluate.

Contents, kept short and factual:

1. **Funnel semantics** — dedup rule and its tiebreak, why file order is never consulted,
   `assigned_at` eligibility, the fixed 24h anchor, greedy-earliest selection and why it is
   optimal, rate denominators, `null` for zero denominators, one-decimal rounding.
2. **Race handling** — the three guard checks and their order, why `classifyReport` must run
   before folding the revision, and why `resyncRevision` is the only sanctioned way the known
   revision moves backwards.
3. **How to run** — `npm start`, the static server, `npm test`, `npm run build`, and `npm run e2e`
   including that it needs Playwright, skips without it, and uses its own ports.
4. **Known limitations** — no persistence, `revision` resets on restart (and how the client
   recovers), the fixed three-step funnel, and that percentages carry no confidence intervals.

Explicitly *not* a rewrite of `README.md`: that file is the exercise specification and stays as
the candidate received it.

---

## 4. Acceptance-criteria audit

A table mapping all 15 criteria to the specific evidence that satisfies them — test name and file,
or the code path plus the e2e scenario. Produced by walking the README criteria one at a time
against the suite, not from memory. Any criterion without a named test is either given one in this
phase or reported as an honest gap.

Preliminary read (to be confirmed during the audit, not assumed):

| AC | Expected evidence |
| --- | --- |
| 1 API + UI | `routes.test.js` funnel contract; e2e oracle test |
| 2 segments, exclusions ineligible | `funnel.test.js` segment tests; `experimentService.test.js` |
| 3 `assigned_at`, unassigned ignored | `funnel.test.js` eligibility tests |
| 4 deterministic dedup | `funnel.test.js` duplicate tests + `NOTES.md` (§3) |
| 5 ordering, repeated steps | `funnel.test.js` ordering tests |
| 6 24h window | `funnel.test.js` boundary + re-anchor tests |
| 7 counts, safe percentages | `funnel.test.js` rates; **new** e2e `—` test (§2.1) |
| 8 file-order independence, rounding | `funnel.test.js` seeded-shuffle tests |
| 9 revision in responses, client tracks newest | `experimentService.test.js`; **new** e2e monotonicity during normal flow (§2.4), with the restart reset as a documented exception |
| 10 bounded `delay_ms` | `routes.test.js` parse table; **new** ceiling test (§2.3) |
| 11 stale response never rendered | `routes.test.js` ordering proof; e2e race tests; **new** refetch test (§2.2) |
| 12 segment race | e2e segment race test |
| 13 exclusion reconciles report | e2e exclusion race test |
| 14 failure keeps last-good report | e2e failure test |
| 15 existing behavior intact | all pre-Phase-1 tests unmodified; e2e validation test |

---

## 5. Repo hygiene

- **Phase docs.** `plan.md` and `phase*-work.md` are five files of planning material. They are
  useful as a record of reasoning but are not part of the application. **Decision needed from the
  user:** keep them, move them under `docs/`, or drop them from the final branch.
- **Stray files.** `backend/` (dead `__pycache__` from a different exercise) and `smoke-test.md`
  (not authored by me) are untracked. Leave both alone unless the user says otherwise — deleting
  files I did not create is not mine to decide.
- **Debug leftovers.** Grep the diff for `console.log`, `debugger`, `.only`, `.skip` and stray
  timeouts before the final commit.
- **`scripts/verify-build.js`.** Confirm the list covers every shipped module (10) and that
  `e2e/` is deliberately excluded, since it is not part of the app.

---

## 6. Final verification protocol

Run in this order, and record the actual output rather than asserting success:

1. `npm test` — expect 51 (50 + §2.3).
2. `npm run e2e` — expect 10 (7 + §2.1, §2.2, §2.4), with per-test isolation.
3. `npm run build` — expect 10 modules.
4. **Re-run the Phase 3 and Phase 5 mutation checks**, since both suites changed:
   - route sleep moved before compute → the routes ordering test must fail;
   - both staleness guards disabled → both e2e race tests must fail.
   A guard that has not been seen to fail since its last edit is unverified.
5. `npm run e2e` a second time, to confirm isolation actually holds and nothing is order- or
   state-dependent.
6. `git status` — confirm only intended files changed.

---

## 7. Exit criteria

- All three suites green, with the counts above.
- Both mutation checks re-confirmed red-then-green.
- `NOTES.md` present and accurate.
- Every acceptance criterion mapped to named evidence, or the gap reported explicitly.
- No `src/` or `web/` changes — or, if Phase 6 forced one, a clear report of what was wrong.
