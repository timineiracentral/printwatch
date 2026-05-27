from fastapi import APIRouter

from app.api.v1 import (
    cost_centers,
    departments,
    export,
    health,
    jobs,
    printers,
    stats,
)

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_v1_router.include_router(
    cost_centers.router, prefix="/cost-centers", tags=["cost-centers"]
)
api_v1_router.include_router(
    departments.router, prefix="/departments", tags=["departments"]
)
api_v1_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_v1_router.include_router(export.router, prefix="/export", tags=["export"])
api_v1_router.include_router(health.router, prefix="/health", tags=["health"])
