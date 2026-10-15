# WaveSend — HARD 60-minute AI-assisted full-stack interview

## Context
WaveSend is an internal outreach operations console. A customer success team maintains SMS campaigns for customer cohorts. Sending the same text to a phone twice, contacting someone after an opt-out, or retrying after a lost response can create serious customer and compliance incidents. The challenge is to ship a credible operator workflow, not to integrate an actual SMS gateway.

## Existing behavior (already working)
The Node.js 20+ application uses a standard-library HTTP API, in-memory state, and a dependency-free browser UI. It already lists three campaigns, filters and searches contacts by name/phone/ID, displays contact details, and edits operator notes. Note edits require `expectedRevision`, trim whitespace, return 409 for stale revisions, and increment the contact and dataset revisions once on a real change, never on a no-op. Slow responses from an earlier filter or contact selection must not replace more recent views. Preserve these behaviors, route contracts, and revision rules.

## Supplied data
- `fixtures/workspace.json`: three SMS campaigns and twelve contacts, including duplicate physical phone numbers, inactive contacts, bad phone data, segment differences, note revisions, and a synthetic `simulation` value for each contact.
- `fixtures/consent_events.jsonl`: unordered consent evidence. Network replay produces duplicate event IDs; events have source, effective time and received time.
- `fixtures/send_history.jsonl`: earlier queued, delivered, and failed attempts, possibly belonging to other campaigns.

Restarting the server resets all state. No network access, database, npm install, credentials or SMS service is needed.

## Customer/business problem
A success manager wants to message the `launch` audience at a chosen instant. Before dispatch, they must see **exactly which phone numbers will be eligible, why others are excluded, and the effect of the two-messages-per-24-hours limit**. The manager may retry after a network timeout. Meanwhile another operator may update a contact, and the emulated delivery provider may accept some messages but reject others. The browser must never display an older preview as the current one.

## Primary feature request
Add **one end-to-end server-authoritative campaign audience preview and dispatch workflow** to the existing application. Operators select a campaign and an explicit instant, preview the eligible recipient list with exclusion explanations, and dispatch the *reviewed* selection exactly once using a request key. Return per-recipient provider outcomes; refresh authoritative state and preserve operator input on failure. This exercise is explicitly **60 minutes, AI-assisted**: you may use Codex, Claude Code, ChatGPT or other tools, but be ready to justify correctness, complexity, assumptions, tests, and incomplete tradeoffs during a walkthrough.

## Acceptance criteria
1. Add `POST /api/campaigns/:id/preview` with `{at,maxRecipients?,delayMs?}` and `POST /api/campaigns/:id/dispatch` with `{previewId,expectedRevision,requestKey,delayMs?}`. `at` must be an ISO-8601 timestamp with explicit `Z` or an offset; `maxRecipients` defaults to 50 and must be an integer 1–100; `delayMs` is an optional integer 0–1200. Clearly distinguish validation errors, unknown campaigns, paused campaigns, stale revisions and reused keys.
2. Preview is **read-only** and returns an opaque preview ID; campaign ID, campaign and dataset revisions, evaluation instant, eligible selected recipients in deterministic order, excluded contact IDs with explicit reasons, counts, and any cap truncation. A paused campaign cannot be previewed for dispatch. Do not decide eligibility in the browser.
3. Normalize US/Canada phone numbers: ten ASCII digits, or eleven ASCII digits beginning with `1`, allowing spaces, `+`, periods, parentheses and hyphens; emit `+1` followed by ten digits. Reject all other strings as invalid numbers (including letters, extensions and ambiguous international numbers). Multiple contacts can share one physical number.
4. Evaluate consent **as of `at`**, not based on line order or arrival order. `kind` is one of `global_opt_in`, `global_opt_out`, `sms_opt_in`, `sms_opt_out`. Each ID's latest received replay wins by received instant, then lexicographically greater canonical JSON payload when tied. If the same event ID claims different contact IDs, that evidence is invalid and must not silently opt anyone in. Only effective times <= `at` count. For each contact and consent scope (global vs SMS), the latest effective instant wins; ties use source priority `legal > support > self_service`, then received instant, then event ID lexicographically ascending. A global opt-in clears only global suppression; it does not imply an SMS opt-in. A contact without an effective SMS opt-in is not eligible.
5. Evaluate active contacts in the campaign's exact segment. For each normalized phone, consider *all* contacts sharing it (even contacts in another segment or archived) for applicable opt-out evidence. An effective global or SMS opt-out on **any** contact sharing that number suppresses the entire phone group. Never send to an archived contact. If several active, in-segment contacts share an otherwise eligible number, pick the lowest contact ID as its representative. Send at most once per physical phone within this dispatch.
6. Apply a **rolling 24-hour cap** to each physical phone across all campaigns, using queued and delivered history only. Count timestamps in `(at - 24 hours, at]`. Failed prior attempts do not count; a send at exactly the lower boundary does not count. Include earlier accepted dispatches in subsequent previews. A blocked phone must have a clear reason.
7. Sort eligible representatives by canonical phone ascending, then contact ID ascending; take at most `maxRecipients` after filtering. Ordering and exclusion reasons must be reproducible under shuffled fixture rows and equivalent UTC offset timestamps. Rejected/malformed evidence must not crash unrelated recipients.
8. Dispatch **only the server-held reviewed preview**: reject missing/expired/unknown preview IDs, a different campaign, or previews whose observed campaign or dataset revision differs from current state. `expectedRevision` must match the reviewed campaign revision. Never trust a client-supplied recipient list, counts, or monetary/eligibility claims. Preview IDs may expire after 15 minutes of server wall-clock time; document your implementation's behavior.
9. Normalize `requestKey` by trimming; require 8–64 nonempty characters. An identical `(campaignId,requestKey)` retry with identical dispatch parameters must return the original authoritative outcome without repeating provider attempts or modifying revisions—even if state changed later. Reuse with different parameters must return 409. Check recorded retries **before** stale-state rejection.
10. For the deterministic simulated provider, `simulation=accepted` queues one SMS record; `transient` returns a retryable failure without recording a send; `rejected` returns a terminal failure without recording a send. Report all per-recipient outcomes in a single dispatch response in preview order. One recipient's failure must not prevent others from being attempted. Do not call any external service. Do not automatically retry failures within the same request.
11. If at least one message queues, append history and increment campaign and dataset revisions **exactly once per dispatch**, regardless of how many recipients were accepted. If none queues, keep both revisions unchanged. Contact revisions and operator notes must remain unchanged. Invalid/stale/duplicate requests must cause no additional mutation.
12. UI: choose campaign and explicit `at`, preview explanations and candidate recipient list, confirm dispatch, display partial successes/failures, surface stale and retry errors, and reconcile the displayed campaign revision and newly included send history. Protect against older delayed preview/dispatch responses overriding a newer selection or operation. A failed call must not erase the user's current controls.
13. Retain the existing contacts search/filter, list/detail selection, note editing, revision/no-op semantics, and HTTP health route. Add focused tests for semantics and the error/race paths you actually implement.

## Constraints
Think at production scale: up to **200,000 contacts**, **400,000 consent events**, **1,000,000 send-history records**, 50,000 contacts per segment, and repeated previews per campaign. Aim for under **500 ms** per preview after startup, excluding intentional artificial delay, and under **256 MB additional process memory** for these datasets. The checked-in fixtures are compact. Avoid a fresh nested full scan of event/history data per contact. Out-of-order, repeated and malformed data are realistic. Server state is authoritative.

## Expected deliverable
Working API + domain behavior + browser flow + focused tests, with any unresolved edge cases explained in the walkthrough. Keep the app runnable with no third-party packages. Meaningful partial completion and sound reasoning count more than an untested one-shot implementation.

## Scope / out of scope
In scope: one SMS campaign preview-to-dispatch feature, deterministic consent/history evaluation, errors, idempotency, concurrency and client synchronization. Out of scope: real messaging, user authentication, databases, background jobs, non-US phone parsing, consent-law interpretation, email campaigns, a marketing analytics platform, and deployment infrastructure.

## Setup / verification
```bash
./scripts/test.sh
./scripts/build.sh
./scripts/verify.sh
./scripts/run.sh
```
Open `http://localhost:8080`. The starter is expected to pass all three checks **before any changes**. Use `PORT=8090 ./scripts/run.sh` if port 8080 is taken. Baseline tests cover existing behavior only; they are not a checklist for the requested feature. Start your **60-minute timer** after reading this README and inspecting the app and fixture structure.
