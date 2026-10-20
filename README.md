# ShiftPay — HARD 60-minute AI-assisted full-stack interview

## Context
ShiftPay is an operations console for a logistics employer with hourly employees across facilities. Supervisors review approved, draft, and voided shift records before payroll closes. Incorrect imported punches or unpaid breaks can change not only one shift's paid minutes but an employee's weekly overtime classification.

## Existing behavior
The **starter application is already runnable** with Node.js 20+, a standard-library HTTP API, fixture-backed in-memory state, and a dependency-free browser UI. Supervisors can filter shifts by employee and status, search ID/name/facility/note, open shift details, inspect elapsed paid minutes, and edit internal notes. Note updates trim whitespace, require `expectedRevision`, reject stale edits with HTTP 409, increment shift and dataset revisions once on a real change, and leave both unchanged on a no-op. Earlier list/detail responses should not overwrite a newer filter or selection. Preserve these working flows.

## Supplied data
`fixtures/workspace.json` contains the deterministic synthetic seed for three generated employees and eleven shifts spanning multiple UTC workdays and payroll weeks, including an overnight shift crossing Monday, different approval states, unpaid breaks, revision history and notes. The seed is expanded by the existing domain bootstrap. Restarting the server restores this snapshot. The frontend, domain layer, HTTP routes, and tests are included.

## Customer/business problem
An approved punch may have the wrong start, end, or unpaid-break times. A payroll operator needs to preview the downstream weekly totals before accepting a correction. Multiple operators may edit a note or correct another shift while the first operator is reviewing. A network timeout may occur after the server has accepted a correction, and the user may retry. The correction must not double-change payroll totals or silently overwrite new information.

## Primary feature request
Implement **one end-to-end preview-and-apply punch correction workflow** across domain, HTTP API, and browser. Operators choose an approved shift, enter a corrected time range and zero to four unpaid breaks with a reason, preview how the proposed change affects that employee's paid/regular/overtime minutes by payroll week, and submit exactly the reviewed correction using a retry-safe request key. Show the authoritative receipt and current shift after success. The starter does **not** implement this feature.

## Acceptance criteria
1. Expose `POST /api/shifts/:id/corrections/preview` accepting `{startAt,endAt,breaks,reason}`. Preview must not mutate state. Return an opaque `previewId`, original and proposed shift values, paid-minute differences, the employee's before/after per-week totals for affected payroll weeks, observed shift and dataset revisions, and a precise explanation of validation errors.
2. Expose `POST /api/shifts/:id/corrections` accepting `{previewId,expectedShiftRevision,expectedDatasetRevision,requestKey,delayMs?}`. On success, return an immutable correction receipt, authoritative updated shift, affected week totals, and new revisions. Validate the input and clearly distinguish HTTP 400, 404, and 409. Any failure is atomic.
3. Only `approved` shifts of active employees are eligible. `draft` and `void` shifts remain visible but ineligible. Both endpoints must reject missing/unknown shift IDs, unsupported fields, invalid or stale preview IDs, cross-shift preview reuse, and changed approval status; the browser must not perform payroll calculations on behalf of the server.
4. `startAt` and `endAt` must be ISO-8601 strings with an explicit `Z` or numeric UTC offset, whole-minute precision and a valid instant. Require strictly increasing endpoints, a duration of at most 16 hours, and at least one paid minute. Compare instants, not textual timestamps. A user-provided offset does not change the payroll week's timezone.
5. `breaks` must be an array of 0–4 `{startAt,endAt}` intervals. Each interval must have the same timestamp validity, be strictly positive, and be fully contained in the corrected shift's half-open `[start,end)` interval. Reject overlapping breaks even if given in reverse order; touching endpoints are allowed. Never count an unpaid minute twice. Reject a corrected shift overlapping another approved shift of the same employee, even if that overlap falls within an unpaid break. Draft and void shifts do not block corrections.
6. `reason` is trimmed, requires 8–160 characters, and is included in the audit receipt. Paid minutes are elapsed minutes minus the minutes in validated unpaid breaks. All durations are integer minutes with no floating-point time rounding.
7. Weekly payroll boundaries are **Monday 00:00 UTC**. Allocate each worked minute to its UTC payroll week, splitting both a shift and any unpaid interval that crosses the boundary. For an employee in each week, the first 2,400 worked minutes are regular and the remainder overtime. Recalculate weekly totals from all approved shifts, not only the corrected one. Before/after summaries must include every week impacted by the original **or** proposed time range and use ascending week-start ordering. Do not calculate pay in dollars.
8. The corrected record keeps its ID, employee ID, approval status and note; replace its start/end/breaks only. Append exactly one correction audit entry with normalized inputs, reason, original values, and computed effects. Successful application increments that shift's revision and the dataset revision exactly once, regardless of how many payroll weeks are affected. All other shifts remain unchanged.
9. `requestKey` must be trimmed, 8–64 characters, unique across the process. The identity of a successful request includes the target shift ID, preview ID, observed revisions and the preview's normalized correction intent. A same-key/same-intent retry returns the **original receipt** without another mutation, even after later edits; a same-key/different-intent retry returns 409. Reusing a failed key after correcting inputs is allowed. Optional `delayMs` is an integer from 0 to 1200 inclusive.
10. A preview only authorizes its exact normalized correction for its observed shift and dataset revisions. Recheck revisions immediately before mutation, **after** any delay. A simultaneous note edit or another correction must produce 409 and no partial work. Concurrent requests with the same key must not apply twice. A preview can be committed at most once except for idempotent replay of its original success.
11. The browser must let operators edit start/end/breaks and reason, request a server preview, compare before/after weekly figures and submit the exact preview. Editing inputs or switching selected shifts invalidates the displayed preview. Prevent accidental duplicate submissions and preserve draft values on timeout or conflict. After 409, refresh authoritative data and allow the user to re-preview intentionally.
12. An obsolete list/detail/preview/commit response must not repaint a newer employee filter or shift selection. After success, refresh shift details and list without a full-page reload. Preserve existing note edit behavior, existing filters, sorting, error responses and starter tests.
13. Add meaningful tests for weekday boundaries, an overnight Sunday-to-Monday shift, offset-equivalent timestamps, touching/overlapping breaks, simultaneous shifts, unavailable approval states, overtime crossing 2,400 minutes, idempotent retries, stale edits after delay, two simultaneous commits, and frontend stale responses. A typical production snapshot may have 150,000 employees and 3 million shifts; avoid scanning unrelated employees for each preview.

## Constraints and expected deliverable
Node.js 20+, single-process memory only, standard library and native browser ES modules; no database, queue, framework, timezone library, external API, auth service, or extra installation. Deliver a usable domain/API/UI vertical slice with focused tests and an explanation of accuracy, complexity, indexing, concurrency, and failure recovery. The candidate owns the design and prioritization.

## Out of scope
Money/pay rates, statutory overtime regimes, local-time payroll weeks, employee pay policy negotiation, rounding to payroll increments, cross-facility permissions, persistence, distributed locking, audit export and visual redesign.

## Setup / run / test
No `npm install` needed:

```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```

Open `http://localhost:8080`. To use another port, run `PORT=8081 ./scripts/run.sh`.

## Explicit 60-minute AI-assisted interview instruction
You have **exactly 60 minutes**. Claude Code, Codex, ChatGPT or another coding assistant is permitted. Inspect the working app, data, tests and API behavior first. Clarify assumptions aloud, implement incrementally, check observable invariants, verify regression behavior, and prepare to defend tradeoffs and limitations in a post-hour walkthrough. A naive one-shot implementation is unlikely to satisfy all constraints.
