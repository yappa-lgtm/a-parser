import re
from typing import Optional

from fastapi import UploadFile

from core.exceptions import NoFilePresentedException, FileValidationException
from core.schemas.main_service_center_mvs_ukraine import (
    MainServiceCenterMVSUkraineDriverLicence,
    MainServiceCenterMVSUkraineCarInfo,
    MainServiceCenterMVSUkraineProcessedCarInfo,
    MainServiceCenterMVSUkrainePersonInfo,
)
from libs.xls_parser import XlsParser
from utils.text_chain import TextChain
from utils.validate_file import validate_file


class MainServiceCenterMVSUkraine:
    async def process(
        self,
        driver_license_file: Optional[UploadFile],
        car_info_file: Optional[UploadFile],
    ) -> MainServiceCenterMVSUkrainePersonInfo:
        if driver_license_file is None and car_info_file is None:
            raise NoFilePresentedException()

        driver_license = None
        cars: list[MainServiceCenterMVSUkraineCarInfo] = []

        if driver_license_file:
            validate_file(driver_license_file, [".xls"], max_size_mb=5)
            driver_license = await self._parse_driver_license_file(driver_license_file)

        if car_info_file:
            validate_file(car_info_file, [".xls"], max_size_mb=5)
            cars = await self._parse_car_info_file(car_info_file)

        if car_info_file and driver_license:
            car_full_name = cars[0].full_name
            driver_license_full_name = f"{driver_license.last_name} {driver_license.first_name} {driver_license.patronymic}"

            if car_full_name != driver_license_full_name:
                raise FileValidationException(
                    filename=car_info_file.filename,
                    reason=f"Не збігається ПІБ ({car_full_name}) з файлом: '{driver_license_file.filename}' ({driver_license_full_name}).",
                )

        has_driver_licence = driver_license is not None

        driver_licence_series = getattr(driver_license, "series", None)
        driver_licence_number = getattr(driver_license, "number", None)
        driver_licence_issue_date = getattr(driver_license, "issue_date", None)
        driver_licence_expiration_date = getattr(
            driver_license, "expiration_date", None
        )
        driver_licence_issued_by = getattr(driver_license, "issued_by", None)
        driver_licence_categories = getattr(driver_license, "categories", None)

        full_name_source = (
            cars[0].full_name
            if cars
            else f"{getattr(driver_license, 'last_name', '')} {getattr(driver_license, 'first_name', '')} {getattr(driver_license, 'patronymic', '')}"
        )
        full_name = (
            TextChain(full_name_source).capitalize_each_word().shorten_full_name().get()
        )

        registration_place_source = (
            getattr(driver_license, "registration_place", None)
            if driver_license
            else cars[0].registration_place
        )
        registration_place = (
            TextChain(registration_place_source)
            .clean_whitespace()
            .capitalize_each_word()
            .normalize_address()
            .get()
        )

        has_more_than_one_car = len(cars) > 0

        processed_cars = [
            MainServiceCenterMVSUkraineProcessedCarInfo(
                plate_number=TextChain(car.plate_number)
                .normalize_document_number()
                .get(),
                vendor=car.vendor,
                year=car.year,
                registration_date=car.registration_date,
                body_number=car.body_number,
                transfer=TextChain(car.transfer)
                .cut_between(start="- ")
                .cut_between(end=" (")
                .normalize_reserved_words()
                .get(),
                color=TextChain(car.color).cut_between("- ").normalize_color().get(),
                is_first=(i == 0),
            )
            for i, car in enumerate(cars)
        ]

        return MainServiceCenterMVSUkrainePersonInfo(
            has_driver_licence=has_driver_licence,
            driver_licence_series=driver_licence_series,
            driver_licence_number=driver_licence_number,
            driver_licence_issue_date=driver_licence_issue_date,
            driver_licence_expiration_date=driver_licence_expiration_date,
            driver_licence_issued_by=driver_licence_issued_by,
            driver_licence_categories=driver_licence_categories,
            full_name=full_name,
            registration_place=registration_place,
            has_more_than_one_car=has_more_than_one_car,
            cars=processed_cars,
        )

    async def _parse_car_info_file(
        self, car_info_file: UploadFile
    ) -> list[MainServiceCenterMVSUkraineCarInfo]:
        content = await car_info_file.read()
        parser = XlsParser(content)

        first_row = parser.cell(row=0, col=0)

        if first_row == "РЕЄСТРАЦІЙНА КАРТКА ТЗ":
            return self._parse_single_car_info(parser)

        if first_row == 'Результати аналітичного пошуку ТЗ по "НАІС ДДАІ" МВС України':
            return self._parse_multi_car_info(parser)

        raise FileValidationException(
            filename=car_info_file.filename,
            reason="Не вірний файл. Не знайдено потрібні ключові слова.",
        )

    @staticmethod
    def _parse_multi_car_info(
        parser: XlsParser,
    ) -> list[MainServiceCenterMVSUkraineCarInfo]:
        cars: list[MainServiceCenterMVSUkraineCarInfo] = []

        for first_col, second_col, third_col, *rest in parser.df.iloc[8:].itertuples(
            index=False, name=None
        ):
            plate_number = first_col.split("\n", 1)[0]
            registration_date = (
                m.group(1)
                if (m := re.search(r"(\d{2}\.\d{2}\.\d{4})", first_col))
                else None
            )
            vendor = (
                TextChain(
                    m.group(1)
                    if (m := re.search(r"^(.+?), \(\d{4}\),", second_col))
                    else None
                )
                .clean_whitespace()
                .get()
            )

            year = m.group(1) if (m := re.search(r"\((\d{4})\)", second_col)) else None

            color = (
                m.group(1).split("-")[-1]
                if (m := re.search(r"\),\s*([\wÀ-ÿІЇЄА-Яа-яʼ']+),", second_col))
                else None
            )

            body_number = (
                m.group(1)
                if (m := re.search(r"№ куз\. *([A-Z0-9]+)", second_col))
                else None
            )

            transfer = (
                m.group(1) if (m := re.search(r"(\d+ - .+)", second_col)) else None
            )

            registration_place = (
                m.group(1) if (m := re.search(r"\n(.+)$", third_col)) else None
            )

            full_name = (
                m.group(1).strip()
                if (m := re.search(r"^([А-ЯІЇЄA-Z\sʼ']+),", third_col))
                else None
            )

            birth_date = (
                m.group(1)
                if (m := re.search(r"нар\.\s*(\d{2}\.\d{2}\.\d{4})", third_col))
                else None
            )

            cars.append(
                MainServiceCenterMVSUkraineCarInfo(
                    plate_number=plate_number,
                    registration_date=registration_date,
                    vendor=vendor,
                    year=year,
                    color=color,
                    body_number=body_number,
                    transfer=transfer,
                    full_name=str(full_name),
                    registration_place=registration_place,
                    birth_date=birth_date,
                )
            )

        return cars

    @staticmethod
    def _parse_single_car_info(
        parser: XlsParser,
    ) -> list[MainServiceCenterMVSUkraineCarInfo]:
        plate_number = parser.cell(row=1, col=2)
        registration_date = parser.cell(row=2, col=2)
        vendor = parser.cell(row=5, col=2)
        year = parser.cell(row=8, col=2)
        color = parser.cell(row=9, col=2)
        body_number = parser.cell(row=10, col=2)
        transfer = parser.cell(row=21, col=2)
        full_name = parser.cell(row=24, col=2)
        registration_place = parser.cell(row=25, col=2)
        birth_date = parser.cell(row=26, col=2)

        return [
            MainServiceCenterMVSUkraineCarInfo(
                plate_number=plate_number,
                registration_date=registration_date,
                vendor=vendor,
                year=year,
                color=color,
                body_number=body_number,
                transfer=transfer,
                full_name=full_name,
                registration_place=registration_place,
                birth_date=birth_date,
            )
        ]

    @staticmethod
    async def _parse_driver_license_file(
        driver_license_file: UploadFile,
    ) -> MainServiceCenterMVSUkraineDriverLicence:
        content = await driver_license_file.read()
        parser = XlsParser(content)

        if parser.cell(row=0, col=0) != "Результат Пошука ПВ":
            raise FileValidationException(
                filename=driver_license_file.filename,
                reason="Не вірний файл. Не знайдено потрібні ключові слова.",
            )

        last_name = parser.cell(row=4, col=1)
        first_name = parser.cell(row=4, col=2)
        patronymic = parser.cell(row=4, col=3)
        birth_date = parser.cell(row=4, col=12)
        series = parser.cell(row=4, col=14)
        number = parser.cell(row=4, col=15)
        issue_date = parser.cell(row=4, col=16)
        expiration_date = parser.cell(row=4, col=17)
        issued_by = parser.cell(row=4, col=18)
        categories = parser.cell(row=4, col=19)
        registration_place = parser.cell(row=4, col=22)
        status = parser.cell(row=4, col=24)

        return MainServiceCenterMVSUkraineDriverLicence(
            last_name=last_name,
            first_name=first_name,
            patronymic=patronymic,
            birth_date=birth_date,
            series=series,
            number=number,
            issue_date=issue_date,
            expiration_date=expiration_date,
            issued_by=issued_by,
            categories=categories,
            registration_place=registration_place,
            status=status,
        )
