from fastapi import APIRouter

from app.simpress.api import cnpjs, contacts, health

simpress_router = APIRouter()
simpress_router.include_router(health.router, prefix="/health")
simpress_router.include_router(cnpjs.router, prefix="/cnpjs")
simpress_router.include_router(contacts.router, prefix="/contacts")
