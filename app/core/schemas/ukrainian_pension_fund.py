from datetime import datetime

from .base import BaseSchema


class UkrainianPensionFundPayment(BaseSchema):
    month: str
    insurer_code: str
    insurer_name: str
    is_insurer_person: bool
    is_last: bool


class UkrainianPensionFundPersonInfo(BaseSchema):
    full_name: str
    is_male: bool
    has_payments: bool
    payments: list[UkrainianPensionFundPayment]
