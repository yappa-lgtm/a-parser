from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_fields = []

    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"][1:])
        if field_path:
            error_fields.append(field_path)

    if error_fields:
        message = f"Невірні дані запиту в полях: {', '.join(error_fields)}"
    else:
        message = "Невірні або відсутні дані запиту"

    return JSONResponse(
        status_code=422,
        content={"message": message},
    )
