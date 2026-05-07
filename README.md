# SolarInspect AI Backend

MVP backend for SolarInspect AI, a multimodal triage copilot for solar panel inspections.

This API is built for fast hackathon iteration with local storage, in-memory inspection state, FastAPI background tasks, and mocked services. It does **not** provide a definitive technical diagnosis. The current behavior is AI-assisted triage designed for human review.

## What Is Implemented

- FastAPI application under `api/`
- CORS enabled for frontend integration
- Swagger/OpenAPI at `/docs`
- `GET /health`
- `GET /ready`
- `POST /api/v1/inspections`
- local upload storage under `storage/uploads/`
- in-memory inspection registry for the MVP
- background processing trigger using `BackgroundTasks`
- mock classifier and VLM readiness flags

## Project Structure

```text
api/
  main.py
  schemas.py
  services/
    __init__.py
    classifier.py
    inspections.py
    reports.py
    storage.py
    vlm.py

storage/
  uploads/
  outputs/
  reports/
```

## Requirements

- Python 3.13 recommended
- PowerShell on Windows

Dependencies are listed in `requirements.txt`:

- `fastapi`
- `uvicorn[standard]`
- `python-multipart`
- `pydantic`
- `python-dotenv`

## How To Run

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api.main:app --reload
```

If the virtual environment already exists, just activate it:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

If port `8000` is busy, use another port:

```powershell
uvicorn api.main:app --reload --port 8001
```

## Local URLs

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI schema: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

If you run on another port, replace `8000` accordingly.

## Endpoints

### `GET /health`

Response:

```json
{
  "status": "ok",
  "service": "solarinspect-api"
}
```

### `GET /ready`

Response:

```json
{
  "status": "ready",
  "storage_ready": true,
  "classifier_ready": false,
  "vlm_ready": false
}
```

### `POST /api/v1/inspections`

Accepts `multipart/form-data` with:

- `plant_name`: string
- `inspection_type`: `thermal`, `rgb`, or `mixed`
- `files`: one or more image files

Allowed file extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.tif`
- `.tiff`

Behavior:

- validates at least one uploaded file
- validates file extensions
- creates an inspection id in the format `insp_YYYYMMDD_HHMMSS_xxxxxx`
- creates `storage/uploads/{inspection_id}/`
- stores uploaded files locally
- creates an in-memory inspection record with status `queued`
- triggers mock background processing

Example response:

```json
{
  "inspection_id": "insp_20260507_153000_ab12cd",
  "status": "queued",
  "plant_name": "Demo Solar Plant",
  "inspection_type": "thermal",
  "total_images": 10,
  "message": "Inspection created successfully."
}
```

## Quick Test

Run these commands after the server is up:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
```

Then test `POST /api/v1/inspections` from Swagger at `/docs`.

Expected checks:

- `/health` returns `ok`
- `/ready` returns `storage_ready=true`
- `/docs` opens normally
- uploaded files appear under `storage/uploads/{inspection_id}/`

## Current MVP Notes

- No database yet
- No Celery or Redis
- No real classifier integration yet
- No real VLM integration yet
- Inspection state is reset when the server restarts

## Next Suggested Backend Steps

- add `GET /api/v1/inspections/{inspection_id}`
- add `GET /api/v1/inspections/{inspection_id}/results`
- add report generation in `services/reports.py`
- replace mocks with real model integrations later
