from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status


ALLOWED_FILE_TYPES = {
    ".pdf": {
        "application/pdf",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    ".txt": {
        "text/plain",
    },
    ".md": {
        "text/markdown",
        "text/plain",
    },
    ".csv": {
        "text/csv",
        "application/csv",
        "text/plain",
        "application/vnd.ms-excel",
    },
}


@dataclass(frozen=True)
class ValidatedFile:
    original_filename: str
    extension: str
    mime_type: str
    size: int


async def validate_upload_file(
    file: UploadFile,
) -> ValidatedFile:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file extension: {extension}",
        )

    content_type = file.content_type or "application/octet-stream"

    allowed_mime_types = ALLOWED_FILE_TYPES[extension]

    if content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Invalid MIME type '{content_type}' "
                f"for extension '{extension}'"
            ),
        )

    

    await file.seek(0)
    content = await file.read()
    size = len(content)
    await file.seek(0)

    validate_file_signature(
        extension=extension,
        content=content,
    )

    return ValidatedFile(
        original_filename=filename,
        extension=extension.lstrip("."),
        mime_type=content_type,
        size=size,
    )


def validate_file_signature(
    extension: str,
    content: bytes,
) -> None:
    if extension == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file signature",
            )

    if extension == ".docx":
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOCX file signature",
            )
