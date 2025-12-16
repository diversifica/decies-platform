import os
import uuid

from fastapi import UploadFile


class StorageService:
    STORAGE_ROOT = "storage"

    @classmethod
    def save_file(cls, file: UploadFile, subfolder: str = "uploads") -> str:
        """
        Saves file to disk and returns the relative path (URI).
        """
        # Ensure directory exists
        path = os.path.join(cls.STORAGE_ROOT, subfolder)
        os.makedirs(path, exist_ok=True)

        # Generate unique filename to avoid collision
        ext = file.filename.split(".")[-1] if file.filename else "bin"
        unique_name = f"{uuid.uuid4()}.{ext}"

        full_path = os.path.join(path, unique_name)

        with open(full_path, "wb") as f:
            f.write(file.file.read())

        return f"{subfolder}/{unique_name}"
