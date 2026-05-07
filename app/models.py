from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ImageType(str, Enum):
    infrared = "infrared"
    rgb = "rgb"
    unknown = "unknown"


class OperationalCategory(str, Enum):
    healthy = "healthy"
    surface_obstruction = "surface_obstruction"
    structural_fault = "structural_fault"
    electrical_fault = "electrical_fault"
    unknown = "unknown"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class InspectionStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Priority(str, Enum):
    monitor = "monitor"
    soon = "soon"
    urgent = "urgent"
    immediate = "immediate"


class BoundingBox(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class StoredImage(BaseModel):
    image_id: str
    filename: str
    content_type: str | None = None
    image_type: ImageType = ImageType.unknown
    path: Path
    image_url: str


class ImageAnalysisResult(BaseModel):
    image_id: str
    filename: str
    image_type: ImageType
    raw_label: str
    category: OperationalCategory
    severity: Severity
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox | None = None
    evidence: list[str]
    explanation: str
    recommended_action: str
    image_url: str
    annotated_image_url: str | None = None


class Inspection(BaseModel):
    inspection_id: str
    status: InspectionStatus
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    image_count: int
    images: list[StoredImage]
    results: list[ImageAnalysisResult] = Field(default_factory=list)
    error: str | None = None
    report_markdown_url: str | None = None
    report_json_url: str | None = None
