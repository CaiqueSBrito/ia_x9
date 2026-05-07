from enum import Enum
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadyResponse(BaseModel):
    status: str
    storage_ready: bool
    classifier_ready: bool
    vlm_ready: bool


class InspectionType(str, Enum):
    thermal = "thermal"
    rgb = "rgb"
    mixed = "mixed"


class InspectionCreateResponse(BaseModel):
    inspection_id: str
    status: str
    plant_name: str
    inspection_type: InspectionType
    total_images: int
    message: str


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ImageResultResponse(BaseModel):
    image_id: str
    filename: str
    image_type: str
    raw_label: str
    category: str
    severity: str
    priority: int
    confidence: float
    bbox: BoundingBox | None
    evidence: str
    explanation: str
    recommended_action: str
    uncertainty: str
    image_url: str
    annotated_image_url: str | None = None


class InspectionStatusResponse(BaseModel):
    inspection_id: str
    plant_name: str
    inspection_type: str
    status: str
    progress: int
    total_images: int
    processed_images: int
    created_at: str
    updated_at: str
    error_message: str | None = None


class InspectionResultsResponse(BaseModel):
    inspection_id: str
    status: str
    results: list[ImageResultResponse]


class ReportResponse(BaseModel):
    inspection_id: str
    report_status: str
    report_url: str
