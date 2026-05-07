from datetime import datetime
from time import sleep
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from api.schemas import InspectionType
from api.services.classifier import ClassifierService, classifier_service
from api.services.storage import StorageService, storage_service
from api.services.vlm import VLMService, vlm_service


INSPECTIONS: dict[str, dict] = {}


PRIORITY_BY_SEVERITY = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "healthy": 4,
    "unknown": 5,
}


class InspectionService:
    def __init__(
        self,
        storage: StorageService,
        classifier: ClassifierService,
        vlm: VLMService,
    ) -> None:
        self.storage = storage
        self.classifier = classifier
        self.vlm = vlm

    async def create_inspection(
        self,
        plant_name: str,
        inspection_type: InspectionType,
        files: list[UploadFile],
    ) -> dict:
        inspection_id = self._create_inspection_id()
        saved_images = await self.storage.save_inspection_uploads(inspection_id, files)
        now = self._now()

        inspection = {
            "inspection_id": inspection_id,
            "plant_name": plant_name,
            "inspection_type": inspection_type.value,
            "status": "queued",
            "total_images": len(saved_images),
            "processed_images": 0,
            "created_at": now,
            "updated_at": now,
            "error_message": None,
            "images": saved_images,
            "results": [],
        }
        INSPECTIONS[inspection_id] = inspection
        return inspection

    def get_inspection(self, inspection_id: str) -> dict:
        inspection = INSPECTIONS.get(inspection_id)
        if inspection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection '{inspection_id}' was not found.",
            )
        return inspection

    def get_inspection_status_payload(self, inspection_id: str) -> dict:
        inspection = self.get_inspection(inspection_id)
        return {
            "inspection_id": inspection["inspection_id"],
            "plant_name": inspection["plant_name"],
            "inspection_type": inspection["inspection_type"],
            "status": inspection["status"],
            "progress": self._calculate_progress(inspection),
            "total_images": inspection["total_images"],
            "processed_images": inspection["processed_images"],
            "created_at": inspection["created_at"],
            "updated_at": inspection["updated_at"],
            "error_message": inspection["error_message"],
        }

    def get_inspection_results_payload(self, inspection_id: str) -> dict:
        inspection = self.get_inspection(inspection_id)
        ordered_results = sorted(
            inspection["results"],
            key=lambda result: (result["priority"], result["image_id"]),
        )
        return {
            "inspection_id": inspection["inspection_id"],
            "status": inspection["status"],
            "results": ordered_results,
        }

    def process_inspection(self, inspection_id: str) -> None:
        inspection = INSPECTIONS.get(inspection_id)
        if inspection is None:
            return

        try:
            inspection["status"] = "processing"
            inspection["updated_at"] = self._now()

            for image in inspection["images"]:
                classifier_result = self.classifier.classify_image(image["path"])
                vlm_result = self.vlm.explain_finding(image["path"], classifier_result)

                result = {
                    "image_id": image["image_id"],
                    "filename": image["filename"],
                    "image_type": self._resolve_image_type(
                        inspection["inspection_type"],
                        image["filename"],
                    ),
                    "raw_label": classifier_result["raw_label"],
                    "category": classifier_result["category"],
                    "severity": classifier_result["severity"],
                    "priority": self._priority_from_result(classifier_result),
                    "confidence": classifier_result["confidence"],
                    "bbox": classifier_result["bbox"],
                    "evidence": classifier_result["evidence"],
                    "explanation": vlm_result["explanation"],
                    "recommended_action": vlm_result["recommended_action"],
                    "uncertainty": vlm_result["uncertainty"],
                    "image_url": image["image_url"],
                    "annotated_image_url": self._to_storage_url(
                        classifier_result["annotated_image_path"]
                    ),
                }

                inspection["results"].append(result)
                inspection["processed_images"] += 1
                inspection["updated_at"] = self._now()
                sleep(0.05)

            inspection["status"] = "completed"
            inspection["updated_at"] = self._now()
        except Exception as exc:
            inspection["status"] = "failed"
            inspection["error_message"] = str(exc)
            inspection["updated_at"] = self._now()

    def _create_inspection_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = uuid4().hex[:6]
        return f"insp_{timestamp}_{suffix}"

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _priority_from_result(self, classifier_result: dict) -> int:
        category = classifier_result.get("category", "unknown")
        if category == "healthy":
            return PRIORITY_BY_SEVERITY["healthy"]
        severity = classifier_result.get("severity", "unknown")
        return PRIORITY_BY_SEVERITY.get(severity, PRIORITY_BY_SEVERITY["unknown"])

    def _resolve_image_type(self, inspection_type: str, filename: str) -> str:
        if inspection_type != "mixed":
            return inspection_type

        lower_name = filename.lower()
        if any(token in lower_name for token in ("thermal", "therm", "ir", "infrared", "flir")):
            return "thermal"
        return "rgb"

    def _to_storage_url(self, annotated_image_path: str | None) -> str | None:
        if not annotated_image_path:
            return None
        return annotated_image_path.replace("\\", "/")

    def _calculate_progress(self, inspection: dict) -> int:
        total_images = inspection["total_images"]
        if total_images == 0:
            return 0
        progress = int((inspection["processed_images"] / total_images) * 100)
        return min(progress, 100)


inspection_service = InspectionService(storage_service, classifier_service, vlm_service)
