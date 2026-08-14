from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..store import store
from ..services import DomainError
from ..settlement_service import build_preview, commit_preview

router = APIRouter(prefix='/api/settlements')


class PreviewBody(BaseModel):
    csv_text: str


class CommitBody(BaseModel):
    preview_id: str


@router.post('/preview')
def preview_settlement(body: PreviewBody):
    try:
        return build_preview(store, body.csv_text)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status, detail={'code': exc.code, 'message': exc.message})


@router.post('/commit')
def commit_settlement(body: CommitBody):
    try:
        return commit_preview(store, body.preview_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status, detail={'code': exc.code, 'message': exc.message})
