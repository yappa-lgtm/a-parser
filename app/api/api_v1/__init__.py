from fastapi import APIRouter

from core.config import settings

from .migration_service import router as migration_service_router
from .ukrainian_pension_fund import router as ukrainian_pension_fund_router
from .main_service_center_mvs_ukraine import (
    router as main_service_center_mvs_ukraine_router,
)
from .healthcheck import router as healthcheck_router

router = APIRouter(prefix=settings.api.v1.prefix)

router.include_router(
    migration_service_router, prefix=settings.api.v1.migration_service
)
router.include_router(
    ukrainian_pension_fund_router, prefix=settings.api.v1.ukrainian_pension_fund
)
router.include_router(
    main_service_center_mvs_ukraine_router,
    prefix=settings.api.v1.main_service_center_mvs_ukraine,
)
router.include_router(healthcheck_router, prefix=settings.api.v1.healthcheck)
