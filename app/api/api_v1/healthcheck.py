from fastapi import APIRouter, status

from core.schemas.healthcheck import HealthCheck

router = APIRouter(tags=["HealthCheck"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")
