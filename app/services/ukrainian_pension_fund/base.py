from datetime import datetime
from xml.etree.ElementTree import Element

from fastapi import UploadFile
from pydantic import ValidationError

from core.exceptions import ValidationException
from core.schemas.ukrainian_pension_fund import (
    UkrainianPensionFundPayment,
    UkrainianPensionFundPersonInfo,
)
from utils.text_chain import TextChain
from utils.validate_file import validate_file
import xml.etree.ElementTree as ET


class UkrainianPensionFundService:
    async def process(
        self, personal_income_file: UploadFile
    ) -> UkrainianPensionFundPersonInfo:
        validate_file(personal_income_file, [".xml", ".XML"], max_size_mb=5)

        content = await personal_income_file.read()

        root = ET.fromstring(content)

        try:
            return self._parse_person_info(root)
        except ValidationError as e:
            raise ValidationException.from_pydantic(e)

    def _parse_person_info(self, root: Element) -> UkrainianPensionFundPersonInfo:
        last_name = root.findtext("LAST_NAME")
        first_name = root.findtext("FIRST_NAME")
        patronymic = root.findtext("SECOND_NAME")
        tax_id = root.findtext("IPN")

        full_name = f"{last_name} {first_name[0]}.{patronymic[0]}."

        if tax_id and len(tax_id) >= 9:
            is_male = int(tax_id[8]) % 2 != 0
        else:
            is_male = None

        payments = self._parse_payments(root)

        ranged_payments = self._process_range_payments(payments)

        return UkrainianPensionFundPersonInfo(
            full_name=full_name,
            is_male=is_male,
            has_payments=len(ranged_payments) > 0,
            payments=ranged_payments,
        )

    @staticmethod
    def _parse_payments(root: Element) -> list[UkrainianPensionFundPayment]:
        payments_root = root.find("PAYMENTS")
        payments: list[UkrainianPensionFundPayment] = []

        if payments_root is None:
            return payments

        payment_elements = payments_root.findall("PAYMENT")
        total = len(payment_elements)

        for idx, payment_el in enumerate(payment_elements):
            month = (
                TextChain(payment_el.findtext("MONTH")).format_connected_date().get()
            )
            insurer_code = payment_el.findtext("INSURER_CODE")
            insurer_name = (
                TextChain(payment_el.findtext("INSURER_NAME"))
                .normalize_ukrainian_chars()
                .shorten_organization_name()
                .normalize_quotes()
                .get()
            )

            payments.append(
                UkrainianPensionFundPayment(
                    month=month,
                    insurer_code=insurer_code,
                    insurer_name=insurer_name,
                    is_last=idx == total - 1,
                    is_insurer_person=len(insurer_code) == 10,
                )
            )

        return payments

    def _process_range_payments(
        self, payments: list[UkrainianPensionFundPayment]
    ) -> list[UkrainianPensionFundPayment]:
        sorted_payments = sorted(
            payments, key=lambda _payment: datetime.strptime(_payment.month, "%d.%m.%Y")
        )

        grouped_by_insurer: dict[str, list[UkrainianPensionFundPayment]] = {}
        for payment in sorted_payments:
            if payment.insurer_name not in grouped_by_insurer:
                grouped_by_insurer[payment.insurer_name] = []
            grouped_by_insurer[payment.insurer_name].append(payment)

        new_payments: list[UkrainianPensionFundPayment] = []

        for insurer_name, payments in grouped_by_insurer.items():
            periods = self._find_consecutive_periods(payments)

            periods_text_list = []

            for period in periods:
                if len(period) == 1:
                    periods_text_list.append(period[0].month)
                else:
                    start_date = period[0].month
                    end_date = period[-1].month
                    periods_text_list.append(f"{start_date} по {end_date}")

            periods_text = ", ".join(periods_text_list)

            new_payments.append(
                UkrainianPensionFundPayment(
                    month=f"з {periods_text}",
                    insurer_code=payments[0].insurer_code,
                    insurer_name=insurer_name,
                    is_insurer_person=payments[0].is_insurer_person,
                    is_last=False,
                )
            )

        return new_payments

    @staticmethod
    def _find_consecutive_periods(
        payments: list[UkrainianPensionFundPayment],
    ) -> list[list[UkrainianPensionFundPayment]]:
        if not payments:
            return []

        periods: list[list[UkrainianPensionFundPayment]] = []
        current_period: list[UkrainianPensionFundPayment] = [payments[0]]

        for i in range(1, len(payments)):
            current_date = datetime.strptime(payments[i].month, "%d.%m.%Y")
            previous_date = datetime.strptime(payments[i - 1].month, "%d.%m.%Y")

            if previous_date.month == 12:
                next_month = previous_date.replace(year=previous_date.year + 1, month=1)
            else:
                next_month = previous_date.replace(month=previous_date.month + 1)

            if current_date == next_month:
                current_period.append(payments[i])
            else:
                periods.append(current_period)
                current_period = [payments[i]]

        periods.append(current_period)
        return periods
