import logging

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from core.config import settings

from api import router as api_router
from core.exception_handlers import validation_exception_handler

logging.basicConfig(format=settings.logging.log_format)

main_app = FastAPI()

main_app.exception_handler(RequestValidationError)(validation_exception_handler)

main_app.include_router(api_router, prefix=settings.api.prefix)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", host=settings.run.host, port=settings.run.port, reload=True
    )
