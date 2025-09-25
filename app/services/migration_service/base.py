import re
import base64
from datetime import datetime
from typing import Optional
from pydantic import ValidationError

from translitua import translit

from core.exceptions import FileValidationException, ValidationException
from core.schemas.migration_service import (
    MigrationServicePersonInfo,
    MigrationServiceDocument,
)
from libs.pdf_parser import PdfParser
from fastapi import UploadFile, File

from utils.text_chain import TextChain
from utils.text_parser import parse_field
from utils.validate_file import validate_file


class MigrationService:
    async def process(self, personal_info_file: UploadFile = File(...)) -> any:
        validate_file(personal_info_file, [".pdf"], max_size_mb=5)

        content = await personal_info_file.read()

        parser = PdfParser(personal_info_file.filename, content)

        self._verify_file(parser)

        self._remove_water_marks(parser)

        clear_text = self._remove_extra_text(parser.text())

        file_text = self._remove_duplicate_rows(clear_text)

        try:
            person_info = self._parse_person_info(file_text, parser)
        except ValidationError as e:
            raise ValidationException.from_pydantic(e)

        return person_info

    def _parse_person_info(
        self, text: str, parser: PdfParser
    ) -> MigrationServicePersonInfo:
        last_name = parse_field(text, "Прізвище", ["Ім`я"])
        first_name = parse_field(text, "Ім`я", ["По батькові"])
        patronymic = parse_field(text, "По батькові", ["Дата народження"])
        genitive_fullname = (
            TextChain(f"{last_name} {first_name} {patronymic}")
            .capitalize_each_word()
            .get()
        )
        translit_fullname = self._translit_full_name(last_name, first_name, patronymic)

        gender = parse_field(text, "Стать", ["УНЗР"])
        is_male = gender == "чоловіча"

        phone = parse_field(text, "Телефон", ["Місце народження"])
        is_phone = bool(phone)

        tax_id = parse_field(text, "РНОКПП", ["Телефон"])
        is_tax_id = bool(tax_id)

        birth_date = parse_field(text, "Дата народження", ["Стать"])

        birth_place = (
            TextChain(parse_field(text, "Місце народження", ["Місце проживання/"]))
            .clean_whitespace()
            .capitalize_each_word()
            .normalize_address()
            .get()
        )

        registration_place = (
            TextChain(
                parse_field(
                    text,
                    "перебування",
                    [
                        "Паспорт громадянина України",
                        "Свідоцтво про народження",
                        "Паспорт(и) громадянина України для виїзду за кордон",
                    ],
                )
            )
            .clean_whitespace()
            .capitalize_each_word()
            .normalize_address()
            .get()
        )

        passports = self._parse_passports(text)
        foreign_passports = self._parse_foreign_passports(text)

        has_passports = len(passports) > 0
        has_foreign_passports = len(foreign_passports) > 0
        has_more_than_one_passport = len(passports) > 1
        has_more_than_one_foreign_passport = len(foreign_passports) > 1

        image_year = self._get_image_year(passports + foreign_passports)

        image = base64.b64encode(parser.get_image_by_index(0)[0]).decode("utf-8")

        cleaned_file = base64.b64encode(parser.save_to_bytes()).decode("utf-8")

        return MigrationServicePersonInfo(
            genitive_fullname=genitive_fullname,
            translit_fullname=translit_fullname,
            gender=gender,
            is_male=is_male,
            phone=phone,
            is_phone=is_phone,
            tax_id=tax_id,
            is_tax_id=is_tax_id,
            birth_date=birth_date,
            birth_place=birth_place,
            registration_place=registration_place,
            has_passports=has_passports,
            has_foreign_passports=has_foreign_passports,
            has_more_than_one_passport=has_more_than_one_passport,
            has_more_than_one_foreign_passport=has_more_than_one_foreign_passport,
            image_year=image_year,
            passports=passports,
            foreign_passports=foreign_passports,
            image=image,
            cleaned_file=cleaned_file,
        )

    @staticmethod
    def _get_image_year(documents: list[MigrationServiceDocument]) -> int:
        image_year = 0

        for document in documents:
            document_year = int(document.issued_at[-4:])

            if document_year > image_year:
                image_year = document_year

        return image_year

    def _parse_passports(self, text: str) -> list[MigrationServiceDocument]:
        return self._parse_document_block(
            self._extract_block(
                text=text,
                start_marker="Паспорт громадянина України",
                end_markers=[
                    "Свідоцтво про народження",
                    "Паспорт(и) громадянина України для виїзду за кордон",
                ],
            )
        )

    def _parse_foreign_passports(self, text: str) -> list[MigrationServiceDocument]:
        return self._parse_document_block(
            self._extract_block(
                text=text,
                start_marker="Паспорт(и) громадянина України для виїзду за кордон",
                end_markers=["Свідоцтво про народження", "Паспорт громадянина України"],
            )
        )

    @staticmethod
    def _extract_block(text: str, start_marker: str, end_markers: list[str]) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        try:
            start_index = next(
                i for i, line in enumerate(lines) if start_marker in line
            )
        except StopIteration:
            return ""

        end_index = next(
            (
                i
                for i, line in enumerate(lines)
                if i > start_index and any(m in line for m in end_markers)
            ),
            -1,
        )

        slice_end = len(lines) if end_index == -1 else end_index
        return "\n".join(lines[start_index + 1 : slice_end])

    def _parse_document_block(self, block: str) -> list[MigrationServiceDocument]:
        if not block:
            return []

        passport_entries = [e for e in re.split(r"(?=Номер)", block) if e.strip()]
        documents: list[MigrationServiceDocument] = []

        def extract(pattern: str, text: str, flags=0) -> Optional[str]:
            match = re.search(pattern, text, flags)
            return match.group(1).strip() if match else None

        for idx, entry in enumerate(passport_entries):
            number = (
                TextChain(extract(r"Номер\s*([\wА-ЯЁЄІЇҐ\-]+)", entry, re.IGNORECASE))
                .normalize_document_number()
                .get()
            )

            issued_at = extract(r"Дата видачі:\s*(\d{2}\.\d{2}\.\d{4})", entry)
            expires_at = self._normalize_document_expires_at(
                extract(r"Дійсний до:\s*([^\n]+)", entry)
            )
            status = extract(r"Стан документа:\s*([^\n]+)", entry)
            issuer = extract(r"Орган видачі:\s*([\s\S]+)", entry)

            if issuer:
                issuer = re.sub(r"\s+", " ", issuer).strip()

            status_bool = True if status and "Дійсний" in status else False

            documents.append(
                MigrationServiceDocument(
                    number=number,
                    issued_at=issued_at,
                    expires_at=expires_at,
                    status=status,
                    issuer=issuer,
                    status_bool=status_bool,
                    is_last=False,
                )
            )

        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                return None

        documents.sort(
            key=lambda d: parse_date(d.issued_at) or datetime.min, reverse=True
        )

        for idx, doc in enumerate(documents):
            doc.is_last = idx == len(documents) - 1

        return documents

    @staticmethod
    def _verify_file(parser: PdfParser) -> None:
        text = parser.text()

        required_phrases = [
            "Державна міграційна служба України",
            "ІНФОРМАЦІЯ ПРО ОСОБУ",
        ]

        if not all(phrase in text for phrase in required_phrases):
            raise FileValidationException(
                filename=parser.filename,
                reason="Не вірний файл. Не знайдено потрібні ключові слова.",
            )

    @staticmethod
    def _remove_water_marks(parser: PdfParser) -> None:
        parser.remove_text(["Користувач "])
        parser.remove_by_operands(["/I2"])

    @staticmethod
    def _remove_extra_text(text: str) -> str:
        data_array = text.split("\n")

        patterns = {"Запит здійснив", "Дата запиту", "Підстава запиту"}

        result = []
        skip_next = False

        for line in data_array:
            if skip_next:
                skip_next = False
                continue

            if line in patterns:
                skip_next = True
                continue

            result.append(line)

        return "\n".join(result)

    @staticmethod
    def _remove_duplicate_rows(text: str) -> str:
        lines = text.split("\n")
        result = [lines[0]]
        for s in lines[1:]:
            if s != result[-1]:
                result.append(s)

        return "\n".join(result)

    @staticmethod
    def _translit_full_name(
        last_name: str, first_name: str, patronymic: Optional[str] = ""
    ) -> str:
        formatted_first = TextChain(first_name).capitalize_each_word().get()
        formatted_patronymic = TextChain(patronymic).capitalize_each_word().get()

        transliterated_last_name = translit(last_name)
        transliterated_first_name = translit(first_name)

        return f"{last_name} ({transliterated_last_name}) {formatted_first} ({transliterated_first_name}) {formatted_patronymic}"

    @staticmethod
    def _normalize_document_expires_at(expires_at: str) -> str:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", expires_at):
            return f"до {expires_at}"
        return expires_at
