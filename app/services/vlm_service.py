from app.models import OperationalCategory, Severity, StoredImage


class MockVLMService:
    """Mock explanation/report text generator, shaped like a future VLM integration."""

    def explain(self, image: StoredImage, classification: dict) -> tuple[str, str]:
        category = classification["category"]
        severity = classification["severity"]

        if category == OperationalCategory.healthy:
            return (
                "The image appears normal in this mock analysis. No immediate anomaly was flagged.",
                "Keep in normal monitoring rotation and review alongside field context.",
            )

        action_by_severity = {
            Severity.low: "Review during the next routine inspection cycle.",
            Severity.medium: "Schedule human review and compare with adjacent module images.",
            Severity.high: "Prioritize technician review and consider targeted field verification.",
            Severity.critical: "Escalate for prompt human review before operational decisions are made.",
        }

        explanation = (
            f"The mock model flagged a {category.value.replace('_', ' ')} pattern with "
            f"{severity.value} severity. This is a triage signal only and should be verified "
            "by a qualified reviewer."
        )
        return explanation, action_by_severity[severity]
