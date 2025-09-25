from dataclasses import dataclass
from typing import Optional, Dict

from core.exceptions import ApplicationException
from pydantic import ValidationError


@dataclass
class ValidationException(ApplicationException):
    status_code: int = 422
    field_errors: Optional[Dict[str, str]] = None

    @property
    def message(self) -> str:
        if not self.field_errors:
            return "Помилка валідації даних"

        error_fields = list(self.field_errors.keys())
        if len(error_fields) == 1:
            return f"Помилка валідації поля: {error_fields[0]}"
        return f"Помилка валідації полів: {', '.join(error_fields)}"

    @classmethod
    def from_pydantic(cls, e: ValidationError) -> "ValidationException":
        field_errors = {
            ".".join(str(loc) for loc in error["loc"]): error["msg"]
            for error in e.errors()
        }
        return cls(field_errors=field_errors)
