from datetime import datetime
from time import sleep
from uuid import uuid4

from fastapi import UploadFile

from api.schemas import InspectionType
from api.services.storage import StorageService, storage_service


INSPECTIONS: dict[str, dict] = {}


class InspectionService:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage

    async def create_inspection(
        self,
        plant_name: str,
        inspection_type: InspectionType,
        files: list[UploadFile],
    ) -> dict:
        inspection_id = self._create_inspection_id()
        saved_files = await self.storage.save_inspection_uploads(inspection_id, files)
        now = self._now()

        inspection = {
            "inspection_id": inspection_id,
            "plant_name": plant_name,
            "inspection_type": inspection_type.value,
            "status": "queued",
            "total_images": len(saved_files),
            "processed_images": 0,
            "created_at": now,
            "updated_at": now,
            "files": saved_files,
        }
        INSPECTIONS[inspection_id] = inspection
        return inspection

    def process_inspection(self, inspection_id: str) -> None:
        inspection = INSPECTIONS.get(inspection_id)
        if inspection is None:
            return

        inspection["status"] = "processing"
        inspection["updated_at"] = self._now()

        for _ in inspection["files"]:
            sleep(0.1)
            inspection["processed_images"] += 1
            inspection["updated_at"] = self._now()

        inspection["status"] = "completed"
        inspection["updated_at"] = self._now()

    def _create_inspection_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = uuid4().hex[:6]
        return f"insp_{timestamp}_{suffix}"

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")


inspection_service = InspectionService(storage_service)
