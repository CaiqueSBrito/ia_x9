from app.services.classifier_service import MockClassifierService
from app.services.inspection_service import InspectionService
from app.services.report_service import ReportService
from app.services.storage_service import StorageService
from app.services.vlm_service import MockVLMService

storage_service = StorageService()
classifier_service = MockClassifierService()
vlm_service = MockVLMService()
inspection_service = InspectionService(storage_service, classifier_service, vlm_service)
report_service = ReportService(storage_service)


def get_storage_service() -> StorageService:
    return storage_service


def get_inspection_service() -> InspectionService:
    return inspection_service


def get_report_service() -> ReportService:
    return report_service
