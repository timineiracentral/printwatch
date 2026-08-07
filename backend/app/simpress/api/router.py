from fastapi import APIRouter

from app.simpress.api import audit, cnpjs, contacts, health, invoices, public_docs, sync

simpress_router = APIRouter()
simpress_router.include_router(health.router, prefix="/health")
simpress_router.include_router(cnpjs.router, prefix="/cnpjs")
simpress_router.include_router(contacts.router, prefix="/contacts")
simpress_router.include_router(public_docs.router, prefix="/public")
simpress_router.include_router(sync.router, prefix="/sync")
simpress_router.include_router(invoices.router, prefix="/invoices")
simpress_router.include_router(audit.router, prefix="/audit")
