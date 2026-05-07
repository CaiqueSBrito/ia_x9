import json
from collections import Counter

from fastapi import HTTPException, status

from app.models import Inspection, InspectionStatus
from app.services.storage_service import StorageService


class ReportService:
    def __init__(self, storage_service: StorageService) -> None:
        self.storage_service = storage_service

    def generate(self, inspection: Inspection) -> tuple[str, str]:
        if inspection.status != InspectionStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report can only be generated after inspection processing is completed.",
            )

        report_dir = self.storage_service.report_dir(inspection.inspection_id)
        markdown_path = report_dir / "report.md"
        json_path = report_dir / "report.json"

        markdown_path.write_text(self._to_markdown(inspection), encoding="utf-8")
        json_path.write_text(
            json.dumps(self._to_json_payload(inspection), indent=2),
            encoding="utf-8",
        )

        return (
            f"/storage/reports/{inspection.inspection_id}/{markdown_path.name}",
            f"/storage/reports/{inspection.inspection_id}/{json_path.name}",
        )

    def _to_markdown(self, inspection: Inspection) -> str:
        category_counts = Counter(result.category.value for result in inspection.results)
        severity_counts = Counter(result.severity.value for result in inspection.results)

        payload = self._summary_payload(inspection, category_counts, severity_counts)

        lines = [
            "# SolarInspect AI Inspection Report",
            "",
            "> Assisted AI triage report. Not a definitive technical diagnosis. Human review is required before operational decisions.",
            "",
            "## Summary",
            "",
            f"- Inspection ID: `{inspection.inspection_id}`",
            f"- Status: `{inspection.status.value}`",
            f"- Images processed: `{inspection.image_count}`",
            "",
            "```json",
            json.dumps(payload, indent=2),
            "```",
            "",
            "## Image Results",
            "",
        ]

        for result in inspection.results:
            lines.extend(
                [
                    f"### {result.filename}",
                    "",
                    f"- Category: `{result.category.value}`",
                    f"- Severity: `{result.severity.value}`",
                    f"- Priority: `{result.priority.value}`",
                    f"- Confidence: `{result.confidence:.2f}`",
                    f"- Raw label: `{result.raw_label}`",
                    f"- Image URL: `{result.image_url}`",
                    "",
                    "**Evidence**",
                    "",
                    *[f"- {item}" for item in result.evidence],
                    "",
                    "**Explanation**",
                    "",
                    result.explanation,
                    "",
                    "**Recommended action**",
                    "",
                    result.recommended_action,
                    "",
                ]
            )

        return "\n".join(lines)

    def _to_json_payload(self, inspection: Inspection) -> dict:
        category_counts = Counter(result.category.value for result in inspection.results)
        severity_counts = Counter(result.severity.value for result in inspection.results)

        return {
            **self._summary_payload(inspection, category_counts, severity_counts),
            "created_at": inspection.created_at.isoformat(),
            "updated_at": inspection.updated_at.isoformat(),
            "results": [result.model_dump(mode="json") for result in inspection.results],
        }

    def _summary_payload(
        self,
        inspection: Inspection,
        category_counts: Counter,
        severity_counts: Counter,
    ) -> dict:
        return {
            "inspection_id": inspection.inspection_id,
            "status": inspection.status.value,
            "image_count": inspection.image_count,
            "category_counts": dict(category_counts),
            "severity_counts": dict(severity_counts),
        }
