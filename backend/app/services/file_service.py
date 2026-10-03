import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class FileService:
    @staticmethod
    def ensure_upload_dir() -> Path:
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    @staticmethod
    def validate_file(file: UploadFile) -> str:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

        ext = Path(file.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        return ext

    @staticmethod
    async def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
        upload_dir = FileService.ensure_upload_dir()
        ext = FileService.validate_file(file)

        unique_filename = f"{uuid.uuid4().hex}{ext}"
        target_path = upload_dir / unique_filename

        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        file_size = 0

        async with aiofiles.open(target_path, "wb") as out_file:
            while content := await file.read(1024 * 64):  # 64KB chunks
                file_size += len(content)
                if file_size > max_size_bytes:
                    # Clean up
                    if target_path.exists():
                        target_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
                    )
                await out_file.write(content)

        relative_path = f"/uploads/{unique_filename}"
        return unique_filename, relative_path, file_size

    @staticmethod
    def delete_file(relative_path: str) -> None:
        filename = Path(relative_path).name
        file_path = Path(settings.UPLOAD_DIR) / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
