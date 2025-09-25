from .base import BaseSchema


class HealthCheck(BaseSchema):
    status: str = "OK"
