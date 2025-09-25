from typing import Optional

from pydantic import Field

from .base import BaseSchema


class MigrationServiceDocument(BaseSchema):
    number: str
    issued_at: str
    expires_at: str
    status: str
    issuer: str
    status_bool: bool
    is_last: bool


class MigrationServicePersonInfo(BaseSchema):
    genitive_fullname: str
    translit_fullname: str
    gender: str
    is_male: bool
    phone: Optional[str] = None
    is_phone: bool
    tax_id: Optional[str] = None
    is_tax_id: bool
    birth_date: str
    birth_place: str
    registration_place: str
    has_passports: bool
    has_foreign_passports: bool
    has_more_than_one_passport: bool
    has_more_than_one_foreign_passport: bool
    image_year: int
    passports: list[MigrationServiceDocument] = Field(default_factory=list)
    foreign_passports: list[MigrationServiceDocument] = Field(default_factory=list)
    image: str
    cleaned_file: str
