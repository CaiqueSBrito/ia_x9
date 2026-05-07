from datetime import datetime

from pydantic import BaseModel

from app.models import ImageAnalysisResult, InspectionStatus


class HealthResponse(BaseModel):
    status: str


class InspectionCreateResponse(BaseModel):
    inspection_id: str
    status: InspectionStatus
    created_at: datetime
    updated_at: datetime
    image_count: int
    message: str


class InspectionResponse(BaseModel):
    inspection_id: str
    status: InspectionStatus
    created_at: datetime
    updated_at: datetime
    image_count: int
    error: str | None = None
    report_markdown_url: str | None = None
    report_json_url: str | None = None


class InspectionResultsResponse(BaseModel):
    inspection_id: str
    status: InspectionStatus
    results: list[ImageAnalysisResult]


class ReportResponse(BaseModel):
    inspection_id: str
    report_markdown_url: str
    report_json_url: str
    message: str
