import logging

from fastapi import APIRouter, UploadFile, File, Depends

from core.dependencies import get_ukrainian_pension_fund_service
from core.exceptions import ApplicationException
from core.schemas.ukrainian_pension_fund import UkrainianPensionFundPersonInfo
from services.ukrainian_pension_fund import UkrainianPensionFundService

router = APIRouter(tags=["Ukrainian Pension Fund"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=UkrainianPensionFundPersonInfo)
async def parse(
    personal_income_file: UploadFile = File(..., alias="personalIncomeFile"),
    service: UkrainianPensionFundService = Depends(get_ukrainian_pension_fund_service),
):
    try:
        result = await service.process(personal_income_file)
        return result
    except ApplicationException as e:
        return e.to_json_response()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ApplicationException().to_json_response()
