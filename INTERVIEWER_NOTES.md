# POST-PRACTICE ONLY — CaptionGate Interviewer Notes

**Never share this with the candidate until after the timed exercise.**

## Intended structure and strong implementation direction
This is a full-stack domain correctness and state-transition exercise, **not** primarily an algorithm puzzle. The core is a small deterministic text parser, canonical caption model, and server-authoritative publish transaction coordinated with a browser draft/review workflow. Candidate decides file organization.

A strong solution normally separates parsing/normalization of WebVTT from validation against an asset, catalog state mutations, HTTP boundary and UI orchestration. Parse input as a sequence of blocks after normalizing BOM and line endings; recognize the initial `WEBVTT` header and skip `NOTE` blocks, then consume optional cue identifier + exact timing line + nonempty text. Convert HH:MM:SS.mmm/MM:SS.mmm into **integer** milliseconds; reject malformed fields/settings. Normalize text as described and use a stable canonical identity `(startMs,endMs,text)`, with identifier conflicts rejected; deduplicate equal cue identities; sort by start/end/text, validate adjacent overlaps and duration boundaries. This is O(B + C log C) for B input bytes and C cues, with O(B + C) working space; limits enforce bounded memory/time.

The backend should store the canonical preview (not client-authored cue arrays) with its studio/asset/locale and asset revision, expiry, consumed state and optional original receipt. Read-only preview shouldn't increment revisions. At publish: normalize key and construct intent; check known successful replay first; validate token, eligibility and expected revision; after optional delay, check again *under one coherent per-process mutation boundary*; compare exact canonical cues with published locale; perform locale replacement or no-op atomically; store immutable outcome under the key. In Node's single event loop, avoid an `await` between final check and mutation, or use a per-asset serializer if introducing additional awaits. Different studios must not access each other's assets. Dataset revision increments on changed writes only, but unrelated assets' dataset changes do not invalidate a preview when the asset revision is unchanged.

The frontend should distinguish **draft** text, **preview** snapshot and **published** captions. Invalidate preview on draft/locale/selection changes; apply request sequence/selection checks to all async responses. Keep request key after an uncertain publish, and avoid generating a new key until a fresh intent. Following a 409, preserve text and allow re-preview rather than automatically overwriting current captions.

## Why naive approaches fail
- Splitting each caption by a fixed number of lines misinterprets optional identifiers, multiline text and NOTE blocks.
- Floating-point seconds lead to imprecise boundaries/overlap checks.
- Sorting strings like `00:59.999` and `01:00:00.000`, or trusting original block order, creates invalid playback ordering.
- A naive overlap detector can reject touching intervals or miss overlaps hidden by out-of-order blocks.
- Replacing captions from a browser-submitted array makes validation bypassable and creates a tampering path.
- Checking revisions before `await setTimeout(delayMs)` allows a concurrent note edit to be overwritten.
- Rechecking staleness before idempotent replay breaks safe retry after a lost successful response.
- Re-using a request key for an altered locale/asset silently assigns the wrong receipt.
- Full-page refresh / global async responses can show stale preview or result for a different studio.
- The existing `readJson` request-size limit is 16 KiB; a correct implementation must account for the specified 128 KiB VTT upper bound without opening an unbounded request-body path.

## Subtle and hidden checks
1. BOM + CRLF plus header description, NOTE with multiple lines, and a multiline Unicode cue. Exact canonical text survives with no broken surrogate pairs.
2. `61:04.500` (hourless minutes >59) is legal, but `01:61:04.500` and `00:01:60.000` are invalid.
3. `00:02.000 --> 00:02.000` invalid; `00:02.000 --> 00:02.001` valid. `00:02.000 --> 00:02.500` and `00:02.500 --> 00:03.000` touch and may coexist.
4. Input in reverse cue order with a nested interval must still fail overlap validation; duplicates removed before overlap checks.
5. Duplicate identifier with changed text or time must produce a validation error; identical semantic cues with different IDs must appear once.
6. End exactly `asset.durationMs` permitted; end 1 ms beyond rejected. Publishing to `processing`/`archived` or unsupported locale denied.
7. Preview has no effect on original captions, note, asset revision or dataset revision; no-op replace also changes none but returns a durable replayable outcome.
8. Studio A cannot read or publish Studio B's asset by guessing the ID, token or request key; retry key scoped to studio yet different intent within studio conflicts.
9. Preview of A-101 (asset rev 3) then note write (rev 4) causes stale publish; editing C-201 must **not** invalidate A-101 merely because dataset revision changed.
10. Preview then delay 800ms; another editor changes note or publishes before the first publish resumes: first must return 409 with no mutation.
11. Two concurrent requests with identical key and token produce one publication and the original receipt twice. A second key on consumed token is rejected.
12. Same key/same intent successful replay after later note change and after preview expiry returns original result. Failed key may be used again after fixing error.
13. Aborted/lost HTTP response after successful commit followed by retry with same key must not double increment revisions; frontend keeps old key.
14. Late preview from one asset or one locale must not overwrite review for another; switching status/search cannot display old list data.
15. A legitimate 128 KiB or near-limit VTT should not be rejected by starter 16 KiB body reader; >128 KiB rejected by bytes, not JS string code units.

## Likely agent failure patterns
A single generative instruction often adds routes without respecting existing note-revision logic; invents an all-new state structure that silently drops other locales; uses loose regexes allowing `abc` timing suffixes; treats cue IDs as text; lets browser store preview from an obsolete selection; or uses a global retry key without intent binding. Model-generated tests may only assert one happy-path file and never exercise stale-after-delay concurrency.

## Fixture discoveries
- A-101 has existing English and Spanish captions, a nonempty note and revision 3: ideal for checking replacement of just French or Spanish without breaking English.
- A-103 and A-104 are intentionally ineligible statuses.
- Studio `cedar` has separate, independent assets and possible overlapping localizations.
- `partner_captions.vtt` uses both timing formats, a NOTE block and multiline cue text; the example is realistic, not a comprehensive parser conformance test.
- Existing note editing increments asset revision and the dataset revision, so it can invalidate the very same asset's preview without a new caption publication.

## Alternative defensible designs
A purpose-built block parser or a cautious state machine are both acceptable. A well-tested limited grammar is better than an overclaimed general WebVTT parser. Snapshot canonical cues in memory or bind tamper-proof deterministic token to an immutable server-side record; both fine as long as replay, expiry and state checks hold. `Map` indexes asset IDs and preview/key records give O(1) lookups; pruning expired tokens is a reasonable extension. If time forces a narrower supported grammar, reward visible evidence and clear error behavior, but do not award correctness for silently accepting unsupported syntax.

## Recommended 60-minute prioritization
0–8 minutes: inspect app, fixtures, note revision contract and HTTP handling. 8–23: parse/normalize + tests for two formats, NOTE, reordering and overlap. 23–38: server preview, eligibility and immutable preview storage. 38–48: atomic publish, conflict checks, idempotent receipt. 48–56: essential browser flow with draft/preview separation. 56–60: run tests/build and state remaining risks. A different prioritization is fine if defended.

## Walkthrough inspection points
Ask: What happens if a token expires after the server has already published? How do you distinguish a replay from key reuse? What is the canonical identity of a cue with an optional ID? Does a title/note change invalidate just that video's preview or all previews? How is half-open overlap checked? Where is the critical section after `delayMs`? What if two requests commit with the same key concurrently? How does the browser avoid rendering a stale preview after selection changes? Can the editor publish 80 KiB of captions with the current body-size limit? Run `./scripts/test.sh`, `./scripts/build.sh` and `./scripts/verify.sh`, inspect regressions, and evaluate evidence of testing rather than breadth of new files.
