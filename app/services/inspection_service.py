from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.models import ImageAnalysisResult, Inspection, InspectionStatus
from app.services.classifier_service import MockClassifierService
from app.services.storage_service import StorageService
from app.services.vlm_service import MockVLMService


class InspectionService:
    def __init__(
        self,
        storage_service: StorageService,
        classifier_service: MockClassifierService,
        vlm_service: MockVLMService,
    ) -> None:
        self.storage_service = storage_service
        self.classifier_service = classifier_service
        self.vlm_service = vlm_service
        self._inspections: dict[str, Inspection] = {}

    async def create_inspection(self, files: list[UploadFile]) -> Inspection:
        self._validate_uploads(files)
        inspection_id = str(uuid4())
        images = await self.storage_service.save_uploads(inspection_id, files)
        inspection = Inspection(
            inspection_id=inspection_id,
            status=InspectionStatus.queued,
            image_count=len(images),
            images=images,
        )
        self._inspections[inspection_id] = inspection
        return inspection

    def get_inspection(self, inspection_id: str) -> Inspection:
        inspection = self._inspections.get(inspection_id)
        if inspection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inspection '{inspection_id}' was not found.",
            )
        return inspection

    def analyze_inspection(self, inspection_id: str) -> None:
        inspection = self.get_inspection(inspection_id)
        self._update_status(inspection, InspectionStatus.processing)

        try:
            results: list[ImageAnalysisResult] = []
            for image in inspection.images:
                classification = self.classifier_service.classify(image)
                explanation, recommended_action = self.vlm_service.explain(image, classification)
                results.append(
                    ImageAnalysisResult(
                        image_id=image.image_id,
                        filename=image.filename,
                        image_type=image.image_type,
                        raw_label=classification["raw_label"],
                        category=classification["category"],
                        severity=classification["severity"],
                        priority=classification["priority"],
                        confidence=classification["confidence"],
                        bbox=classification["bbox"],
                        evidence=classification["evidence"],
                        explanation=explanation,
                        recommended_action=recommended_action,
                        image_url=image.image_url,
                        annotated_image_url=None,
                    )
                )
                inspection.results = results
                inspection.updated_at = self._now()

            self._update_status(inspection, InspectionStatus.completed)
        except Exception as exc:
            inspection.error = str(exc)
            self._update_status(inspection, InspectionStatus.failed)

    def attach_report(self, inspection_id: str, markdown_url: str, json_url: str) -> Inspection:
        inspection = self.get_inspection(inspection_id)
        inspection.report_markdown_url = markdown_url
        inspection.report_json_url = json_url
        inspection.updated_at = self._now()
        return inspection

    def _validate_uploads(self, files: list[UploadFile]) -> None:
        if not files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload at least 5 image files.")
        if len(files) < settings.min_upload_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upload at least {settings.min_upload_files} image files.",
            )
        if len(files) > settings.max_upload_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upload at most {settings.max_upload_files} image files.",
            )
        for file in files:
            if file.content_type and not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{file.filename}' is not an image upload.",
                )

    def _update_status(self, inspection: Inspection, status_value: InspectionStatus) -> None:
        inspection.status = status_value
        inspection.updated_at = self._now()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
