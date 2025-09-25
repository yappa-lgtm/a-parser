from humps import camelize
from pydantic import BaseModel


class BaseSchema(BaseModel):
    class Config:
        alias_generator = camelize
        validate_by_name = True
