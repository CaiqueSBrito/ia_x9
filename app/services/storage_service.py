from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.models import ImageType, StoredImage


class StorageService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or settings.storage_root
        self.uploads_dir = self.root / "uploads"
        self.reports_dir = self.root / "reports"

    def ensure_ready(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def save_uploads(self, inspection_id: str, files: list[UploadFile]) -> list[StoredImage]:
        self.ensure_ready()
        inspection_dir = self.uploads_dir / inspection_id
        inspection_dir.mkdir(parents=True, exist_ok=True)

        stored_images: list[StoredImage] = []
        for upload in files:
            image_id = str(uuid4())
            safe_name = self._safe_filename(upload.filename or f"{image_id}.bin")
            filename = f"{image_id}_{safe_name}"
            path = inspection_dir / filename

            with path.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    target.write(chunk)

            stored_images.append(
                StoredImage(
                    image_id=image_id,
                    filename=filename,
                    content_type=upload.content_type,
                    image_type=self.detect_image_type(upload.filename or filename, upload.content_type),
                    path=path,
                    image_url=f"/storage/uploads/{inspection_id}/{filename}",
                )
            )

        return stored_images

    def report_dir(self, inspection_id: str) -> Path:
        self.ensure_ready()
        path = self.reports_dir / inspection_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def detect_image_type(self, filename: str, content_type: str | None) -> ImageType:
        name = filename.lower()
        if any(token in name for token in ("thermal", "therm", "ir", "infrared", "flir")):
            return ImageType.infrared
        if content_type and content_type.startswith("image/"):
            return ImageType.rgb
        return ImageType.unknown

    def _safe_filename(self, filename: str) -> str:
        allowed = []
        for char in filename:
            if char.isalnum() or char in {".", "-", "_"}:
                allowed.append(char)
            else:
                allowed.append("_")
        return "".join(allowed).strip("._") or "upload.bin"
