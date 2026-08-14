from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..store import store
from ..services import DomainError, find_account, list_account_invoices, record_manual_credit

router = APIRouter(prefix='/api/accounts')

class ManualCreditBody(BaseModel):
    amountCents: int
    reason: str

@router.get('')
def list_accounts():
    return [a.to_dict() for a in store.accounts]

@router.get('/{account_id}')
def get_account(account_id: str):
    account = find_account(store, account_id)
    if not account:
        raise HTTPException(status_code=404, detail={'code': 'account_not_found', 'message': 'account not found'})
    return {
        'account': account.to_dict(),
        'invoices': [i.to_dict() for i in list_account_invoices(store, account_id)],
    }

@router.post('/{account_id}/credits')
def add_manual_credit(account_id: str, body: ManualCreditBody):
    try:
        return record_manual_credit(store, account_id, body.amountCents, body.reason)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status, detail={'code': exc.code, 'message': exc.message})
