import os
from typing import Optional

from fastapi import UploadFile

from core.exceptions import FileValidationException


def validate_file(
    file: UploadFile,
    allowed_extensions: Optional[list[str]] = None,
    max_size_mb: Optional[float] = None,
    min_size_mb: Optional[float] = None,
) -> None:
    filename = file.filename or "<unknown>"

    if not file.filename:
        raise FileValidationException(
            filename=filename, reason="Назва файлу не вказана"
        )

    if allowed_extensions:
        file_ext = os.path.splitext(filename)[1].lower()
        allowed_ext_lower = [ext.lower() for ext in allowed_extensions]

        if file_ext not in allowed_ext_lower:
            raise FileValidationException(
                filename=filename,
                reason=f"Недозволене розширення '{file_ext}'. Дозволені: {', '.join(allowed_extensions)}",
            )

    if hasattr(file, "size") and file.size is not None:
        file_size = file.size

        if min_size_mb:
            min_size_bytes = int(min_size_mb * 1024 * 1024)
            if file_size < min_size_bytes:
                raise FileValidationException(
                    filename=filename,
                    reason=f"Файл занадто малий. Мінімальний розмір: {min_size_mb:.2f} МБ",
                )

        if max_size_mb:
            max_size_bytes = int(max_size_mb * 1024 * 1024)
            if file_size > max_size_bytes:
                raise FileValidationException(
                    filename=filename,
                    reason=f"Файл занадто великий. Максимальний розмір: {max_size_mb:.2f} МБ",
                )
