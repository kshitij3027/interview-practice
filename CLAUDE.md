# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Ledger Lens** is a full-stack billing-operations tool (FastAPI + vanilla JS) used as an interview exercise. The task is to implement a settlement-import workflow on top of the existing starter app. Read `README.md` for the full acceptance criteria before coding.

## Running the app

```bash
# Backend (port 3001)
python -m uvicorn backend.app.main:app --reload --port 3001

# Frontend (separate terminal, port 5173)
python -m http.server 5173 -d frontend
```

Open `http://localhost:5173`.

## Tests and build checks

```bash
# Run all backend tests
pytest -q

# Run a single test file
pytest backend/tests/test_accounts.py -q

# Frontend syntax check
./scripts/verify_frontend.sh
```

## Architecture

### Backend (`backend/`)

- **`app/main.py`** — FastAPI app with CORS for `localhost:5173`. Mounts two routers.
- **`app/models.py`** — Pure dataclasses: `Account`, `Invoice`, `CreditEvent`. Monetary values are stored as integer cents.
- **`app/store.py`** — Single global `store` instance (in-memory, thread-locked). `store.reset()` restores seed data. All routes share this singleton.
- **`app/services.py`** — Domain logic layer. `DomainError` carries `code`, `message`, and HTTP `status`. Routes catch `DomainError` and re-raise as `HTTPException`.
- **`app/routes/`** — Thin route handlers that call services; no domain logic here.
- **`tests/conftest.py`** — `autouse` fixture resets store before/after every test; `client` fixture returns a `TestClient`.

### Frontend (`frontend/`)

- No build step — plain ES modules loaded directly by the browser.
- **`src/store.js`** — Pub/sub state container (`get`, `set`, `subscribe`). Every `set()` call re-renders.
- **`src/api.js`** — Thin fetch wrapper; throws `Error` with `detail.message` on non-OK responses.
- **`src/app.js`** — Top-level: wires store → render, attaches DOM event listeners after each render.
- **`src/accountTable.js` / `src/accountPanel.js`** — Pure render functions returning HTML strings.

### Key conventions

- All money goes through integer cents in the backend; the frontend converts dollars ↔ cents at the boundary (e.g., `Math.round(Number(amount) * 100)`).
- Account `revision` increments on every mutation (credit, settlement commit). This is the optimistic-concurrency key for stale-preview detection.
- `Store.lock` is a `threading.Lock`; acquire it for any multi-step mutation in services.
- New routes go in `backend/app/routes/`; new domain logic goes in `backend/app/services.py` (or a new service module); register new routers in `main.py`.
- New frontend API calls go in `api.js`; new UI state fields go in the `state` object inside `store.js`.

### Settlement feature (the exercise)

The fixture at `fixtures/customer_settlement_aug14.csv` demonstrates the real-world messiness: whitespace/casing on `customer_ref`, duplicate `payment_id` rows, unknown customers, malformed amounts. The feature requires:
- `POST /api/settlements/preview` — pure read, returns a plan with per-row results and account revisions used.
- `POST /api/settlements/commit` — applies the plan; rejects if any account revision has changed since preview.
- Server owns the preview state (don't trust client-sent allocations); idempotent commit (retry-safe).
