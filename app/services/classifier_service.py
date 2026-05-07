from hashlib import sha256

from app.models import BoundingBox, OperationalCategory, Priority, Severity, StoredImage


class MockClassifierService:
    """Deterministic mock classifier for frontend/backend integration."""

    def classify(self, image: StoredImage) -> dict:
        digest = sha256(image.filename.encode("utf-8")).hexdigest()
        bucket = int(digest[:2], 16) % 5

        candidates = [
            {
                "raw_label": "normal_module_temperature",
                "category": OperationalCategory.healthy,
                "severity": Severity.low,
                "priority": Priority.monitor,
                "confidence": 0.91,
                "bbox": None,
                "evidence": ["No obvious hotspot pattern detected in the mock pass."],
            },
            {
                "raw_label": "localized_hotspot_possible_soiling",
                "category": OperationalCategory.surface_obstruction,
                "severity": Severity.medium,
                "priority": Priority.soon,
                "confidence": 0.78,
                "bbox": BoundingBox(x=0.34, y=0.28, width=0.18, height=0.2),
                "evidence": ["Localized contrast pattern suggests possible obstruction or soiling."],
            },
            {
                "raw_label": "crack_or_cell_damage_pattern",
                "category": OperationalCategory.structural_fault,
                "severity": Severity.high,
                "priority": Priority.urgent,
                "confidence": 0.74,
                "bbox": BoundingBox(x=0.2, y=0.42, width=0.36, height=0.12),
                "evidence": ["Linear discontinuity pattern resembles a structural anomaly."],
            },
            {
                "raw_label": "diode_string_hotspot_pattern",
                "category": OperationalCategory.electrical_fault,
                "severity": Severity.critical,
                "priority": Priority.immediate,
                "confidence": 0.82,
                "bbox": BoundingBox(x=0.48, y=0.18, width=0.22, height=0.48),
                "evidence": ["Mock thermal signature aligns with a string-level hotspot pattern."],
            },
            {
                "raw_label": "uncertain_visual_pattern",
                "category": OperationalCategory.unknown,
                "severity": Severity.medium,
                "priority": Priority.soon,
                "confidence": 0.52,
                "bbox": None,
                "evidence": ["Image quality or pattern ambiguity limits confidence."],
            },
        ]
        return candidates[bucket]
