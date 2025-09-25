import logging

from fastapi import APIRouter, UploadFile, File, Depends

from core.dependencies import get_migration_service
from core.exceptions import ApplicationException
from services.migration_service import MigrationService

router = APIRouter(tags=["Migration Service"])

logger = logging.getLogger(__name__)


@router.post("/")
async def parse(
    personal_info_file: UploadFile = File(..., alias="personalInfoFile"),
    service: MigrationService = Depends(get_migration_service),
):
    try:
        result = await service.process(personal_info_file)
        return result
    except ApplicationException as e:
        return e.to_json_response()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ApplicationException().to_json_response()
