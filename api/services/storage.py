from pathlib import Path

from fastapi import HTTPException, UploadFile, status


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class StorageService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("storage")
        self.uploads_dir = self.root / "uploads"
        self.outputs_dir = self.root / "outputs"
        self.reports_dir = self.root / "reports"

    def ensure_directories(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def is_ready(self) -> bool:
        try:
            self.ensure_directories()
        except OSError:
            return False
        return all(
            path.exists() and path.is_dir()
            for path in (self.uploads_dir, self.outputs_dir, self.reports_dir)
        )

    async def save_inspection_uploads(
        self,
        inspection_id: str,
        files: list[UploadFile],
    ) -> list[dict]:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image file must be uploaded.",
            )

        self.ensure_directories()
        inspection_dir = self.uploads_dir / inspection_id
        inspection_dir.mkdir(parents=True, exist_ok=True)

        saved_images: list[dict] = []
        for index, upload in enumerate(files, start=1):
            original_filename = upload.filename or ""
            extension = Path(original_filename).suffix.lower()
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"File '{original_filename or f'file_{index}'}' has an unsupported extension. "
                        "Allowed extensions: .jpg, .jpeg, .png, .webp, .tif, .tiff."
                    ),
                )

            safe_name = self._safe_filename(original_filename)
            filename = f"{index:03d}_{safe_name}"
            target_path = inspection_dir / filename

            with target_path.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    target.write(chunk)

            saved_images.append(
                {
                    "image_id": f"img_{index:03d}",
                    "filename": filename,
                    "path": str(target_path),
                    "image_url": f"/storage/uploads/{inspection_id}/{filename}",
                }
            )

        return saved_images

    def _safe_filename(self, filename: str) -> str:
        cleaned = []
        for char in filename:
            if char.isalnum() or char in {".", "-", "_"}:
                cleaned.append(char)
            else:
                cleaned.append("_")
        return "".join(cleaned).strip("._") or "image"


storage_service = StorageService()
