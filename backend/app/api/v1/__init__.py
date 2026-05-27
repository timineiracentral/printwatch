from fastapi import APIRouter

from app.api.v1 import health, jobs, printers

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_v1_router.include_router(health.router, prefix="/health", tags=["health"])
