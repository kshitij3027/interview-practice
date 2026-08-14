# Settlement Reconciliation — Implementation Plan

## Phase 0: API Contract (do this first, unblocks parallel tracks)

Lock the endpoint shapes before splitting work so frontend and backend don't drift.

**`POST /api/settlements/preview`**
- Request: `{ "csv_text": "..." }`
- Response `200`:
  ```json
  {
    "preview_id": "prev_abc123",
    "rows": [
      { "payment_id": "PAY-901", "status": "valid", "account_id": "acct_1",
        "allocations": [{"invoice_id": "inv_100", "applied_cents": 7500, "remaining_after_cents": 1500}],
        "credit_remainder_cents": 0 },
      { "payment_id": "PAY-902", "status": "duplicate", "error": "duplicate of PAY-902" },
      { "payment_id": "PAY-904", "status": "error", "error": "unknown customer: UNKNOWN-77" }
    ],
    "account_revisions": { "acct_1": 7, "acct_2": 3 }
  }
  ```

**`POST /api/settlements/commit`**
- Request: `{ "preview_id": "prev_abc123" }`
- Response `200`: `{ "status": "committed" | "already_committed", "accounts": [...] }`
- Response `409`: `{ "detail": { "code": "stale_preview", "message": "..." } }`

---

## Phase 1A — Backend (parallel with 1B)

**Step A1: Extend `store.py`**
Add two fields to `Store.__init__` and `reset()`:
```python
self.previews: dict[str, dict] = {}          # preview_id → plan
self.committed_preview_ids: set[str] = set() # idempotency guard
```

**Step A2: Add `backend/app/settlement_service.py`**

Three functions, each independently testable:

`parse_csv(text: str) → list[dict]`
- Split on `\n`, skip empty trailing lines
- Detect header order from first row; fail fast if required columns missing
- Return list of raw row dicts

`build_preview(store, csv_text: str) → dict`
- Parse rows via `parse_csv`
- **Duplicate guard**: iterate in order; first occurrence of a `payment_id` is canonical, later ones get `status: "duplicate"` — no set lookup ambiguity
- **Customer resolution**: `customer_ref.strip().casefold()` matched against `account.external_id.casefold()` — unknown → row-level `status: "error"`, continue
- **Amount validation**: use `decimal.Decimal`, check `> 0` and `quantize(Decimal('0.01'))` round-trips losslessly, convert to cents via `int(amount * 100)` — malformed → row-level `status: "error"`, continue
- **Allocation**: for valid rows, get open invoices for account sorted by `(due_date, id)`, greedily apply cents, track remainder → account credit
- **Snapshot revisions**: read `account.revision` for each affected account into `account_revisions` dict
- Store result in `store.previews[preview_id]` and return it (no other mutations)

`commit_preview(store, preview_id: str) → dict`
- Look up plan or raise `DomainError("preview not found", "preview_not_found", 404)`
- **Idempotency**: if `preview_id in store.committed_preview_ids` → return `{"status": "already_committed", "accounts": [...]}`
- **Under `store.lock`**: re-read each account revision; if any diverges from `plan["account_revisions"]` → raise `DomainError("stale_preview", "stale_preview", 409)`
- Apply mutations atomically: update `invoice.remaining_cents`, set `invoice.status = "paid"` when it hits zero, add `credit_remainder_cents` to `account.credit_cents`, increment `account.revision` exactly once per account
- Add `preview_id` to `store.committed_preview_ids`
- Return `{"status": "committed", "accounts": [...]}`

**Step A3: Add `backend/app/routes/settlements.py`**
Mirrors pattern from `accounts.py` — thin Pydantic body models, call service, catch `DomainError` → `HTTPException`. Register router in `main.py`.

**Step A4: `backend/tests/test_settlements.py`**

Write these test cases (each is a standalone `client` fixture call, store auto-resets):

| Test | What it asserts |
|---|---|
| `test_preview_valid_csv` | All valid rows return `status: valid`, correct allocations, no state mutation |
| `test_preview_does_not_mutate_state` | Call preview, then GET /accounts; revisions and balances unchanged |
| `test_preview_unknown_customer_is_row_error` | Unknown ref → row error; other rows still processed |
| `test_preview_malformed_amount_is_row_error` | `not-a-number` → row error; other rows still processed |
| `test_preview_duplicate_payment_id` | Second PAY-902 gets `status: duplicate`; money not double-counted |
| `test_preview_overpayment_becomes_credit` | Payment exceeds open invoice total → remainder in `credit_remainder_cents` |
| `test_preview_partial_invoice_payment` | Invoice partially paid; `remaining_after_cents` reflects correct residual |
| `test_commit_applies_allocations` | Commit → invoices updated, paid when zero, credit incremented, revision +1 |
| `test_commit_revision_incremented_once_per_account` | Two valid rows for same account → revision incremented exactly once |
| `test_commit_stale_preview_returns_409` | Add manual credit after preview, then commit → 409 `stale_preview` |
| `test_commit_stale_is_atomic` | Stale commit with two accounts: partial apply must not happen; verify neither account changed |
| `test_commit_idempotent` | Second commit of same `preview_id` → `already_committed`, no double-apply |
| `test_manual_credit_after_commit_still_works` | Existing credit endpoint unaffected |

---

## Phase 1B — Frontend (parallel with 1A)

**Step B1: Add settlement state to `store.js`**
```js
csvText: '',
preview: null,         // raw API response {preview_id, rows, account_revisions}
settlementBusy: false,
settlementError: '',
settlementCommitted: false,  // drives post-commit UI
```

**Step B2: Add `api.js` methods**
```js
previewSettlement: (csvText) => fetch(`${API}/settlements/preview`, { method: 'POST', ... }).then(json),
commitSettlement: (previewId) => fetch(`${API}/settlements/commit`, { method: 'POST', ... }).then(json),
```

**Step B3: Add `frontend/src/settlementPanel.js`**
Follows the same pattern as `accountPanel.js` — pure function returning an HTML string:

- **Import section**: `<textarea>` bound to `csvText`, Preview button
- **Preview results table**: one row per input CSV row; status badge (valid / error / duplicate), proposed allocations (invoice id + applied amount), credit remainder
- **Commit button**: only rendered when `preview !== null` and at least one valid row
- **Stale error path**: on 409, preserve `csvText`, show `"Preview is stale — re-submit CSV to get a fresh preview"`, clear `preview`
- **Already-committed path**: show a distinct success message without re-rendering as stale

**Step B4: Wire into `app.js`**
- Import `renderSettlementPanel`, add to `render()` alongside account table
- Add event listeners for preview submit and commit click
- On commit success: call `refresh()` (already exists) to reload accounts and selected detail — no new refresh logic needed
- On stale: `store.set({ preview: null, settlementError: "stale...", csvText: state.csvText })`

---

## Phase 2 — Integration verification (sequential, after both tracks done)

1. Happy path end-to-end: paste fixture CSV → preview → commit → account table updates
2. Stale detection: preview → add manual credit via existing form → commit → should 409, CSV preserved
3. Idempotent retry: commit → commit again → `already_committed` (no double balance change)
4. Duplicate rows: PAY-902 appears twice in fixture — confirm second flagged as duplicate
5. Run `pytest -q` — all tests green including existing ones
6. Run `./scripts/verify_frontend.sh` — JS syntax clean

---

## Key decisions that prevent common bugs

| Risk | Mitigation in plan |
|---|---|
| Race condition on commit | Acquire `store.lock`, re-validate all revisions before first write |
| Partial apply on stale | Revision check is fully inside the lock; zero mutations before all checks pass |
| Double-commit | `committed_preview_ids` set checked before any mutation, inside lock |
| Float rounding drift | `decimal.Decimal` for parsing, integer cents throughout; no float arithmetic |
| Stale UI after commit | Reuse existing `refresh()` which re-fetches both list and detail |
| UI side effects from re-render | Settlement state (`csvText`, `preview`) lives in the same store; every `set()` re-renders atomically |
| Duplicate determinism | First-seen-wins using dict insertion order (Python 3.7+ guaranteed) |
