from fastapi import APIRouter

from app.simpress.api import health

simpress_router = APIRouter()
simpress_router.include_router(health.router, prefix="/health")
