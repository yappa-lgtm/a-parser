import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends

from core.dependencies import get_main_service_center_mvs_ukraine
from core.exceptions import ApplicationException
from core.schemas.main_service_center_mvs_ukraine import (
    MainServiceCenterMVSUkrainePersonInfo,
)
from services.main_service_center_mvs_ukraine import MainServiceCenterMVSUkraine

router = APIRouter(tags=["Main Service Center MVS Ukraine"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=MainServiceCenterMVSUkrainePersonInfo)
async def parse(
    driver_license_file: Optional[UploadFile] = File(None, alias="driverLicenseFile"),
    car_info_file: Optional[UploadFile] = File(None, alias="carInfoFile"),
    service: MainServiceCenterMVSUkraine = Depends(get_main_service_center_mvs_ukraine),
):
    try:
        result = await service.process(
            driver_license_file=driver_license_file, car_info_file=car_info_file
        )
        return result
    except ApplicationException as e:
        return e.to_json_response()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ApplicationException().to_json_response()
