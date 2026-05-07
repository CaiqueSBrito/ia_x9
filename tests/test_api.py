from fastapi.testclient import TestClient

from api.main import app
from api.services.inspections import INSPECTIONS


client = TestClient(app)


def _valid_form_data() -> dict:
    return {
        "plant_name": "Demo Solar Plant",
        "inspection_type": "thermal",
    }


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "solarinspect-api"


def test_ready_returns_200() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"


def test_create_inspection_without_files_returns_error() -> None:
    response = client.post("/api/v1/inspections", data=_valid_form_data())
    assert response.status_code == 400
    assert "At least one image file must be uploaded." in response.json()["detail"]


def test_create_inspection_with_fake_file_returns_inspection_id() -> None:
    files = [("files", ("panel_001.jpg", b"fake-image-bytes", "image/jpeg"))]
    response = client.post("/api/v1/inspections", data=_valid_form_data(), files=files)

    assert response.status_code == 202
    payload = response.json()
    assert payload["inspection_id"].startswith("insp_")
    assert payload["status"] in {"queued", "processing", "completed"}


def test_get_inspection_returns_status() -> None:
    files = [("files", ("panel_002.jpg", b"fake-image-bytes", "image/jpeg"))]
    create_response = client.post("/api/v1/inspections", data=_valid_form_data(), files=files)
    inspection_id = create_response.json()["inspection_id"]

    response = client.get(f"/api/v1/inspections/{inspection_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["inspection_id"] == inspection_id
    assert payload["status"] in {"queued", "processing", "completed", "failed"}


def test_get_inspection_not_found_returns_404() -> None:
    response = client.get("/api/v1/inspections/insp_missing")
    assert response.status_code == 404


def test_full_flow_returns_results_report_and_static_files() -> None:
    files = [
        ("files", ("panel_003.jpg", b"fake-image-bytes-1", "image/jpeg")),
        ("files", ("panel_004.jpg", b"fake-image-bytes-2", "image/jpeg")),
    ]
    create_response = client.post("/api/v1/inspections", data=_valid_form_data(), files=files)
    inspection_id = create_response.json()["inspection_id"]

    status_response = client.get(f"/api/v1/inspections/{inspection_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["progress"] == 100

    results_response = client.get(f"/api/v1/inspections/{inspection_id}/results")
    assert results_response.status_code == 200
    results_payload = results_response.json()
    assert len(results_payload["results"]) == 2
    priorities = [result["priority"] for result in results_payload["results"]]
    assert priorities == sorted(priorities)

    image_url = results_payload["results"][0]["image_url"]
    image_response = client.get(image_url)
    assert image_response.status_code == 200

    report_response = client.post(f"/api/v1/inspections/{inspection_id}/report")
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["report_status"] == "generated"

    static_report_response = client.get(report_payload["report_url"])
    assert static_report_response.status_code == 200
    assert "SolarInspect AI Report" in static_report_response.text
    assert "All findings require human review." in static_report_response.text


def setup_function() -> None:
    INSPECTIONS.clear()
