from services.main_service_center_mvs_ukraine import MainServiceCenterMVSUkraine
from services.migration_service import MigrationService
from services.ukrainian_pension_fund import UkrainianPensionFundService


def get_migration_service() -> MigrationService:
    return MigrationService()


def get_ukrainian_pension_fund_service() -> UkrainianPensionFundService:
    return UkrainianPensionFundService()


def get_main_service_center_mvs_ukraine() -> MainServiceCenterMVSUkraine:
    return MainServiceCenterMVSUkraine()
