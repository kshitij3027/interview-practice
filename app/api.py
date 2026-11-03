"""HTTP routes for the existing operations console."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.store import LotStore, StoreError


BASE = Path(__file__).resolve().parents[1]


def make_app(store=None):
    app = FastAPI(title="BatchGuard")
    state = store or LotStore()
    app.state.lot_store = state

    @app.exception_handler(StoreError)
    async def domain_error(_, exc):
        return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})

    @app.get("/api/meta")
    def meta():
        return {"plants": list(state.plants.values()), "specifications": list(state.specs.values()),
                "datasetRevision": state.dataset_revision}

    @app.get("/api/lots")
    def list_lots(plant: str = "", status: str = "", q: str = "", limit: int = 50):
        return state.list_lots(plant, status, q, limit)

    @app.get("/api/lots/{lot_id}")
    def detail(lot_id: str):
        return state.detail(lot_id)

    @app.patch("/api/lots/{lot_id}/note")
    async def note(lot_id: str, request: Request):
        try:
            body = await request.json()
        except ValueError:
            raise StoreError(400, "BAD_JSON", "Request body must be JSON")
        if not isinstance(body, dict):
            raise StoreError(400, "BAD_BODY", "Expected a JSON object")
        return state.edit_note(lot_id, body.get("note"), body.get("expectedRevision"))

    app.mount("/", StaticFiles(directory=BASE / "public", html=True), name="public")
    return app


app = make_app()
