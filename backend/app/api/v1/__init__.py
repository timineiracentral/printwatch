from fastapi import APIRouter

from app.api.v1 import (
    admin,
    cost_centers,
    cost_rates,
    departments,
    export,
    health,
    import_routes,
    jobs,
    printers,
    stats,
    users,
)

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_v1_router.include_router(
    cost_centers.router, prefix="/cost-centers", tags=["cost-centers"]
)
api_v1_router.include_router(
    cost_rates.router, prefix="/cost-rates", tags=["cost-rates"]
)
api_v1_router.include_router(
    departments.router, prefix="/departments", tags=["departments"]
)
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_v1_router.include_router(export.router, prefix="/export", tags=["export"])
api_v1_router.include_router(health.router, prefix="/health", tags=["health"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_v1_router.include_router(import_routes.router, prefix="/import", tags=["import"])
