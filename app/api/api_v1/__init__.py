from fastapi import APIRouter

from core.config import settings

from .migration_service import router as migration_service_router
from .healthcheck import router as healthcheck_router

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(
    migration_service_router, prefix=settings.api.v1.migration_service
)
router.include_router(healthcheck_router, prefix=settings.api.v1.healthcheck)
