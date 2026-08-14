from fastapi import APIRouter
from ..store import store

router = APIRouter(prefix='/api/invoices')

@router.get('')
def list_invoices():
    return [i.to_dict() for i in store.invoices]
