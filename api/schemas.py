from pydantic import BaseModel
from enum import Enum


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
