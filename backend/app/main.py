from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.accounts import router as accounts_router
from .routes.invoices import router as invoices_router

app = FastAPI(title='Ledger Lens')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(accounts_router)
app.include_router(invoices_router)

@app.get('/api/health')
def health():
    return {'ok': True}
