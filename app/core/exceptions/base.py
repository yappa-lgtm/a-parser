from dataclasses import dataclass
from typing import Dict

from fastapi.responses import JSONResponse


@dataclass
class ApplicationException(Exception):
    status_code: int = 500

    @property
    def message(self) -> str:
        return "Сталася помилка додатку"

    def to_dict(self) -> Dict[str, str]:
        return {"message": self.message}

    def to_json_response(self):
        return JSONResponse(status_code=self.status_code, content=self.to_dict())
