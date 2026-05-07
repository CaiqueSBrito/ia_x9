from fastapi import BackgroundTasks, Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.dependencies import get_inspection_service, get_report_service, get_storage_service
from app.schemas import (
    HealthResponse,
    InspectionCreateResponse,
    InspectionResponse,
    InspectionResultsResponse,
    ReportResponse,
)
from app.services.inspection_service import InspectionService
from app.services.report_service import ReportService
from app.services.storage_service import StorageService

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Assisted multimodal triage API for solar panel inspections. "
        "Mock AI services are used in this MVP."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.storage_root.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.storage_root), name="storage")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/ready", response_model=HealthResponse, tags=["system"])
def ready(storage: StorageService = Depends(get_storage_service)) -> HealthResponse:
    storage.ensure_ready()
    return HealthResponse(status="ready")


@app.post(
    f"{settings.api_prefix}/inspections",
    response_model=InspectionCreateResponse,
    status_code=202,
    tags=["inspections"],
)
async def create_inspection(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    service: InspectionService = Depends(get_inspection_service),
) -> InspectionCreateResponse:
    inspection = await service.create_inspection(files)
    background_tasks.add_task(service.analyze_inspection, inspection.inspection_id)
    return InspectionCreateResponse(
        inspection_id=inspection.inspection_id,
        status=inspection.status,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
        image_count=inspection.image_count,
        message="Inspection created and queued for analysis.",
    )


@app.get(
    f"{settings.api_prefix}/inspections/{{inspection_id}}",
    response_model=InspectionResponse,
    tags=["inspections"],
)
def get_inspection(
    inspection_id: str,
    service: InspectionService = Depends(get_inspection_service),
) -> InspectionResponse:
    inspection = service.get_inspection(inspection_id)
    return InspectionResponse(
        inspection_id=inspection.inspection_id,
        status=inspection.status,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
        image_count=inspection.image_count,
        error=inspection.error,
        report_markdown_url=inspection.report_markdown_url,
        report_json_url=inspection.report_json_url,
    )


@app.get(
    f"{settings.api_prefix}/inspections/{{inspection_id}}/results",
    response_model=InspectionResultsResponse,
    tags=["inspections"],
)
def get_inspection_results(
    inspection_id: str,
    service: InspectionService = Depends(get_inspection_service),
) -> InspectionResultsResponse:
    inspection = service.get_inspection(inspection_id)
    return InspectionResultsResponse(
        inspection_id=inspection.inspection_id,
        status=inspection.status,
        results=inspection.results,
    )


@app.post(
    f"{settings.api_prefix}/inspections/{{inspection_id}}/report",
    response_model=ReportResponse,
    tags=["reports"],
)
def create_report(
    inspection_id: str,
    inspection_service: InspectionService = Depends(get_inspection_service),
    report_service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    inspection = inspection_service.get_inspection(inspection_id)
    markdown_url, json_url = report_service.generate(inspection)
    inspection_service.attach_report(inspection_id, markdown_url, json_url)
    return ReportResponse(
        inspection_id=inspection_id,
        report_markdown_url=markdown_url,
        report_json_url=json_url,
        message="Report generated for human review.",
    )
