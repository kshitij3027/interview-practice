# FieldKit — HARD 60-minute full-stack interview

## Context
A field-service company uses versioned inspection checklists for equipment. A draft inspection is pinned to the template version that existed when work began. Supervisors periodically publish revised checklists.

## Existing behavior
PHP 8.2+ JSON API and a dependency-free browser console. Browse inspections, select one, inspect its pinned form and save or clear individual answers. Saves use a revision check, validate against the pinned schema, preserve revision for no-ops, and reject completed inspections. State is persisted in a local JSON file. Preserve these behaviors, including false and zero answers.

## Customer problem
Technicians must move unfinished inspections to the newest published checklist without losing valid work or silently reinterpreting old answers. They need to review what changes before committing; another browser may edit a draft while the preview is open.

## Primary feature request
Build one end-to-end draft checklist upgrade workflow: preview moving a draft to its template's latest version, show answer retention and losses, then apply the reviewed upgrade and allow editing on the new schema. No upgrade functionality exists yet.

## Supplied data
fixtures/workspace.json has templates (immutable versions keyed by integer version), fields (stable id, label, type, required, optional choices/min/max), and inspections (templateId, version, revision, status, answers, archive). Answers are keyed by field ID, not labels. Inspect the fixtures; ordering and labels change across versions. Versions may be skipped.

## Acceptance criteria
1. Add GET /api/inspections/:id/upgrade returning source version, target version, current revision, target fields in target order, retained answers, discarded answers with reasons, and missing required field IDs in target order. Preview is read-only. Unknown inspection is 404; completed or already-current inspection is 409. Latest means highest numeric version of the same template, not array order.
2. Retain an answer only if its stable ID exists in the target, source and target types are identical, and the value passes target validation. Do not coerce types, map labels, or assume a renamed label means a different field. Choice values are exact case-sensitive strings; integer bounds are inclusive. Zero, false and empty text are valid if the field validator allows them. Absent answers are not discarded. Report discarded answers in source-field order with original value and one reason: removed, type_changed, invalid_value (in that precedence).
3. Missing required fields are those without retained answers or with retained text that is blank after trimming. A false boolean or zero integer is present. Do not invent defaults or block an upgrade merely because required answers need attention. A newly added field must not inherit an archived answer from an earlier version.
4. Add POST /api/inspections/:id/upgrade with JSON {expectedRevision,targetVersion}. Both are integers. The server must independently derive the upgrade from current data; do not trust a client-supplied answer map. Reject a stale revision or target that is no longer latest with 409 and current revision/version; reject invalid input with 400. Apply only to a draft with a newer version. A successful apply atomically changes version, replaces answers, increments revision once and appends one archive entry per discarded answer containing fieldId, value, reason, fromVersion, toVersion. Preserve older archive records. Invalid/stale requests cannot change any state. A repeated old request after a lost response must not archive twice; a conflict followed by refresh is acceptable.
5. UI: show an upgrade affordance on eligible drafts; show target fields/retained values, discarded values and reasons, missing required fields, and confirm/cancel. After success refresh the actual form and show archive and outstanding required answers. Disable confirmation while pending; changes to selection or draft revision invalidate the reviewed preview. On conflict or uncertain network response refresh authoritative state and require a fresh preview if still eligible. Late responses cannot replace another selected inspection. Keep existing edit behavior, including validation against the new pinned form after upgrading.
6. Add focused tests for upgrade semantics and API behavior; demonstrate a stale preview after an ordinary answer save and preservation of historical archive records.

## Constraints
Single local server, JSON state, no external dependencies. Up to 100 fields per version and 20 versions per template; inspect only the relevant template/inspection for upgrade logic. PHP integers, booleans, strings are distinct. Treat fixture versions as immutable. Existing field validator defines accepted values. Empty answer map can be serialized as an empty object or array. Use meaningful error messages.

## Out of scope
Publishing templates, editing completed inspections, automatic migrations, authentication, production storage, schema authoring and completion workflow.

## Setup / run / test
Requires PHP 8.2+, Node 18+ for JS syntax checks and API smoke tests. No package installation.
- Build: `bash scripts/build.sh`
- Tests: `bash scripts/test.sh`
- Verify: `bash scripts/verify.sh`
- Run: `php -S 127.0.0.1:8080 -t public public/router.php`
- Open http://127.0.0.1:8080. Stop server and delete data/state.json to reset.

## Interview instruction
60 minutes, AI assistance permitted. Inspect the working app and data, plan a vertical slice, implement and test incrementally. At the end demonstrate the feature and explain tradeoffs, remaining gaps and verification. Do not spend the hour on styling.
