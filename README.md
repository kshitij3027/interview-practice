# CaptionGate — 60-minute AI-assisted full-stack interview

## Context
CaptionGate is a media-operations console used by two studios to manage localized captions for short-form video. A partner localization team delivers WebVTT exports. Editors need reliable publication: mistimed captions can appear after a video ends, an old translation can overwrite a newer one, and a network timeout can make an editor unsure whether a publish succeeded.

## Existing behavior — already working
This is a working **Node.js 20+ standard-library HTTP app** with in-memory fixture-backed records and a vanilla browser ES-module frontend. Choose a studio, filter assets by status, search by title/series/ID, inspect asset metadata and already-published captions, and edit an internal note. Asset lists sort by title then ID; the total is measured before the result limit. Edited notes are trimmed, require the asset's current revision, and increment the asset and dataset revisions once. Identical note writes are no-ops; stale writes return 409. The UI ignores obsolete list/detail responses after navigation. Preserve these features.

## Supplied data
`fixtures/catalog.json` contains two studios, eight video assets, statuses (`ready`, `processing`, `archived`), durations in milliseconds, supported caption locales, existing published captions, notes and revisions. `fixtures/partner_captions.vtt` is a representative partner export with cue identifiers, two legal timestamp formats, multiline text and a `NOTE` section. Restarting the server restores the fixture. In production, studios may have tens of thousands of assets and translations, but the checked-in sample is intentionally compact.

## Customer/business problem
An editor receives a revised subtitle file for **one video and one supported locale**. Today they cannot see how the supplied cues will appear or validate them before replacing the live captions. They also cannot distinguish an uncertain publish response from a publish that never happened. Other editors might change the asset while a preview is open. They need a usable, accurate, explainable workflow rather than a file upload that silently overwrites state.

## Primary feature request
**Add a review-and-publish workflow for a complete localized WebVTT caption replacement.** Let the editor paste or load text, select a locale, review the server's canonical cues and timing diagnostics without changing the live captions, then publish precisely that reviewed revision. Safely handle conflicts, retries and late browser responses. Implement the coordinated domain/API/UI changes and focused tests. This requested feature does **not** exist in the starter.

## Acceptance criteria — externally observable behavior
1. Add a UI for choosing a supported locale and supplying raw WebVTT text, including pasting or loading the checked-in example. Display a distinct review action, a readable preview (cues, time ranges, counts and warnings/errors), and a publish action. Keep existing asset browsing, caption inspection, and note editing functional.
2. Add `POST /api/assets/:id/captions/preview?studio=<id>` accepting `{locale,vtt}` and returning on success `{previewId,assetId,locale,observedAssetRevision,observedDatasetRevision,cues,summary,expiresAt}`. The `cues` are in canonical display order with `{startMs,endMs,text}`. `summary` includes `cueCount`, `wordCount`, `coveredMs`, and `lastEndMs`. The preview must not mutate published captions or either revision.
3. Add `POST /api/assets/:id/captions/publish?studio=<id>` accepting `{previewId,expectedAssetRevision,requestKey,delayMs?}`. Success returns an immutable publish receipt, the authoritative updated asset, the new dataset revision and an `unchanged` boolean. Failed requests return structured JSON errors (400 malformed, 404 unknown/other-studio asset, 409 conflicts); failures change nothing.
4. Only `ready` assets can be previewed or published. The locale must exactly match one of the asset's `supportedLocales` (case-sensitive). An unknown studio, invalid locale, processing/archived asset, absent file or oversized file must not be treated as a successful preview. A studio cannot inspect or publish another studio's assets.
5. Accept a UTF-8 BOM, `\n` or `\r\n` line endings, a first `WEBVTT` line with optional descriptive text, blank-separated cues, optional identifier line immediately before a timing line, and `NOTE` blocks terminated by a blank line. Support timestamps `MM:SS.mmm` and `HH:MM:SS.mmm`, and a timing delimiter ` --> ` with surrounding spaces. Only `00`–`59` seconds and `00`–`59` minutes are valid when an hour field is present; `MM` may exceed 59 when hours are absent. WebVTT positioning/style directives are not required.
6. A cue must have a valid positive-duration interval and at least one non-whitespace text line. Text retains meaningful Unicode content and multiline breaks; strip leading/trailing whitespace on individual text lines. Empty/invalid cue blocks, malformed time fields, unsupported timing settings and duplicate identifiers with conflicting timing or text must produce understandable input diagnostics rather than silently changing captions. Require at least one valid cue, at most 250 distinct canonical cues, and raw input no larger than 128 KiB in UTF-8.
7. Cue blocks may arrive out of playback order. Produce deterministic canonical order by start milliseconds, end milliseconds, then exact text. Identical normalized cues (even if delivered twice) appear once. Duplicate identifier reuse with *different* normalized cue content is an error. Cue intervals are half-open `[startMs,endMs)`: touching boundaries are permitted, but positive overlap is invalid. No cue may start before zero or end after the video's `durationMs`; ending exactly at the duration is valid. Report precise offending cue or line when input is rejected.
8. Compute preview `wordCount` as the number of nonempty whitespace-delimited tokens across canonical cue texts; `coveredMs` as the total interval duration of canonical nonoverlapping cues; `lastEndMs` as the latest ending timestamp. All time arithmetic uses integer milliseconds, not floating-point seconds. Repeated previews of semantically identical files return the same canonical cues and summary independent of input block order and line endings.
9. A preview token is server-owned, bound to studio, video, locale, canonical cues and asset revision, and expires after 10 minutes. The client must not be able to submit its own cues or amend a token's content, asset, studio or locale. An expired, absent, cross-asset or previously consumed token cannot create a new publication. A preview of an ineligible asset is not publishable.
10. Publishing **replaces only the selected locale's full caption list**. Other locales, asset metadata, notes and other assets remain intact. Successful changed publication increments the asset revision and dataset revision exactly once and returns an auditable receipt containing the locale, old/new cue counts and a server-assigned publish identifier. When published cues already equal canonical reviewed cues, return `unchanged: true` without incrementing either revision. Do not create partial caption writes.
11. Require a trimmed `requestKey` of 8–64 characters, scoped per studio. A successful same-key/same-intent retry returns the **original receipt** (including original revisions and `unchanged` result) without another write, even after later edits. Reusing the key with different asset, locale, token or expected revision returns 409. Failed attempts do not consume keys. Check a known successful replay before rejecting an expired/consumed preview or newer revision.
12. Publish only if the current asset revision still equals `expectedAssetRevision` and the revision captured by the preview. A note update or another caption publication on that same asset makes an older review stale; a change on an unrelated asset does not. `delayMs`, when supplied, is an integer from 0 to 1200; validate and recheck immediately before mutation **after** the delay. Concurrent publications using one token or request key must not double publish or race past checks.
13. In the browser, editing source text or locale invalidates an existing preview. Switching studio/asset or receiving older list/detail/preview/publish responses must not repaint the currently selected asset. Disable duplicate-click submissions. After an uncertain network failure preserve the original preview and request key for a safe retry; after 409 preserve the user's draft and offer an intentional fresh preview. Refresh live captions, revisions and visible list after a successful publish without page reload.
14. Add focused tests for BOM/CRLF, hourless timestamps, invalid seconds, reversed and touching ranges, overlaps after reordering, identifier conflicts, exact duplicates, malformed NOTE/cue blocks, text normalization, out-of-bounds endings, locale isolation, no-op replacement, note-change staleness, concurrent publish, response-loss retries, and existing note/list behavior. For large catalogs, avoid scanning unrelated videos or reparsing the same entire file for every publish attempt. Explain any complexity or resource tradeoffs in your walkthrough.

## Constraints
Maintain Node.js 20+ and the built-in Node APIs, an in-memory single-process backend, fixture-backed state, and plain browser JavaScript. No database, Redis, queue, WebVTT parsing package, React, authentication system, cloud storage, background job, or third-party API. You may extend routes, domain modules, client state and tests. Treat the server as authoritative for validation, ordering, preview tokens, writes and retry results.

## Expected deliverable
A usable vertical slice across the domain model, API and browser; clear validation and conflict UX; focused automated verification; and a short explanation of tradeoffs. A robust partial implementation with explicit limitations is preferable to an unchecked one-shot implementation.

## Out of scope
Video playback and timecode synchronization, live streaming, caption styling, karaoke timing, timestamp maps, voice transcription, translation generation, WebVTT positioning instructions, cross-asset batch publication, authentication, storage after process restart, and multi-process coordination.

## Setup, build, test, verification
No dependency installation is needed.

```bash
./scripts/build.sh
./scripts/test.sh
./scripts/verify.sh
./scripts/run.sh
```

Open `http://localhost:8080`. Set `PORT=8081` to use another port. Existing tests cover the working baseline and intentionally do **not** specify the full feature solution.

## Explicit 60-minute AI-assisted interview instruction
You have **60 minutes**. Claude Code, Codex, ChatGPT or similar tools are permitted. First inspect the existing app, fixtures, APIs and tests. Choose a defensible implementation order, make incremental changes, verify behavior, and be ready to walk through your reasoning about correctness, scalability, retries, and what you would finish with additional time. A happy-path-only parser and publish button are not a complete solution.
