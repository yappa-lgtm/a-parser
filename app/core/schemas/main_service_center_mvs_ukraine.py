from typing import Optional

from .base import BaseSchema


class MainServiceCenterMVSUkraineProcessedCarInfo(BaseSchema):
    plate_number: str
    vendor: str
    year: str
    registration_date: str
    body_number: Optional[str] = None
    transfer: str
    color: str
    is_first: bool


class MainServiceCenterMVSUkrainePersonInfo(BaseSchema):
    has_driver_licence: bool
    driver_licence_series: Optional[str] = None
    driver_licence_number: Optional[str] = None
    driver_licence_issue_date: Optional[str] = None
    driver_licence_expiration_date: Optional[str] = None
    driver_licence_issued_by: Optional[str] = None
    driver_licence_categories: Optional[str] = None
    full_name: str
    registration_place: str
    has_more_than_one_car: bool
    cars: list[MainServiceCenterMVSUkraineProcessedCarInfo]


class MainServiceCenterMVSUkraineDriverLicence(BaseSchema):
    last_name: str
    first_name: str
    patronymic: str
    birth_date: str
    series: str
    number: str
    issue_date: str
    expiration_date: str
    issued_by: str
    categories: str
    registration_place: str
    status: str


class MainServiceCenterMVSUkraineCarInfo(BaseSchema):
    plate_number: str
    registration_date: str
    vendor: str
    year: str
    color: str
    body_number: Optional[str] = None
    transfer: str
    full_name: str
    registration_place: str
    birth_date: str
