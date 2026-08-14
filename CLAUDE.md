# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Dispatch Desk — a starter app for a one-hour full-stack interview exercise. It's an intentionally small delivery-dispatch tool (Express/TypeScript API + React/TypeScript frontend, in-memory persistence) that the candidate extends with a "Claim next job" workflow.

`README.md` has the exercise brief (acceptance criteria, constraints, scope). `INTERVIEWER_NOTES.md` is post-practice-only — do not open it while attempting the exercise (it contains the intended solution and grading notes).

## Commands

Run from the repo root (npm workspaces: `server`, `client`).

- `npm install` — install all workspace deps
- `npm run dev` — run backend (`tsx watch`, port 3001) and frontend (`vite`, port 5173) concurrently
- `npm test` — run backend tests (`vitest run`, in `server/`); there is no client test suite
- `npm run build` — typecheck/build server then client
- Single test file: `npm test -w server -- test/app.test.ts`
- Server only: `npm run dev -w server` / `npm run build -w server`
- Client only: `npm run dev -w client` / `npm run build -w client`

CI (`.github/workflows/validate.yml`) runs on `exercise/**` branches: `npm install`, `npm test`, `npm run build`.

## Architecture

Two npm workspaces, no shared package between them — types are duplicated by hand (`server/src/types.ts` and `client/src/types.ts` both define `DeliveryJob`; keep them in sync manually when changing the API shape).

**Server** (`server/src/`):
- `store.ts` — the entire persistence layer: an in-memory `jobs` array (seeded from `initialJobs`, reset via `resetStore()` for tests) plus pure functions (`listJobs`, `assignJob`) that mutate it. This is where new store operations (e.g. a claim operation) belong — keep mutation logic centralized here rather than in route handlers.
- `app.ts` — `createApp()` builds the Express app and wires routes directly to store functions; no controller/service layer beyond this. Route handlers do request validation (e.g. trimming/rejecting an empty `driver`) and translate store result "kinds" (discriminated unions like `{ kind: "not-found" }` / `{ kind: "already-assigned" }` / `{ kind: "ok", job }`) into HTTP status codes.
- `index.ts` — just calls `createApp().listen(...)`.
- Tests (`server/test/app.test.ts`) hit the app through `supertest` against `createApp()` directly, calling `resetStore()` in `beforeEach`.

**Client** (`client/src/`):
- `api.ts` — thin `fetch` wrappers per endpoint, hardcoded `API_BASE = http://localhost:3001/api`.
- `App.tsx` — single-component app: loads jobs on mount, holds a `driver` name input, renders a card grid, and calls `api.ts` functions directly from event handlers, updating local `jobs` state from the response.
- No router, no state management library, no component splitting beyond `App.tsx` — this is deliberately minimal for interview scope.

## Design constraints to respect when extending

These come from the exercise brief and matter for any change in this repo:

- Keep the in-memory store — no database, queue, or external service.
- The backend is the source of truth; centralize any "find best job" + "assign" logic as one synchronous server-side operation rather than splitting it across client-driven steps.
- Preserve existing manual-assign behavior (`PATCH /api/jobs/:jobId/assign`) exactly.
