from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import HealthResponse, InspectionCreateResponse, InspectionType, ReadyResponse
from api.services.classifier import classifier_service
from api.services.inspections import inspection_service
from api.services.storage import storage_service
from api.services.vlm import vlm_service

app = FastAPI(
    title="SolarInspect AI API",
    version="0.1.0",
    description="Backend API for assisted solar panel inspection triage.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="solarinspect-api")


@app.get("/ready", response_model=ReadyResponse, tags=["system"])
def ready() -> ReadyResponse:
    return ReadyResponse(
        status="ready",
        storage_ready=storage_service.is_ready(),
        classifier_ready=classifier_service.is_ready(),
        vlm_ready=vlm_service.is_ready(),
    )


@app.post(
    "/api/v1/inspections",
    response_model=InspectionCreateResponse,
    status_code=202,
    tags=["inspections"],
)
async def create_inspection(
    background_tasks: BackgroundTasks,
    plant_name: str = Form(...),
    inspection_type: InspectionType = Form(...),
    files: list[UploadFile] | None = File(None),
) -> InspectionCreateResponse:
    inspection = await inspection_service.create_inspection(
        plant_name=plant_name,
        inspection_type=inspection_type,
        files=files or [],
    )
    background_tasks.add_task(
        inspection_service.process_inspection,
        inspection["inspection_id"],
    )

    return InspectionCreateResponse(
        inspection_id=inspection["inspection_id"],
        status=inspection["status"],
        plant_name=inspection["plant_name"],
        inspection_type=inspection["inspection_type"],
        total_images=inspection["total_images"],
        message="Inspection created successfully.",
    )
