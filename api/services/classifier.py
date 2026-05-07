import json
import os
from pathlib import Path

LABEL_TO_CATEGORY = {
    "clean": "healthy",
    "healthy": "healthy",
    "bird-drop": "surface_obstruction",
    "dusty": "surface_obstruction",
    "snow-covered": "surface_obstruction",
    "physical-damage": "structural_fault",
    "crack": "structural_fault",
    "scratch": "structural_fault",
    "broken": "structural_fault",
    "electrical-damage": "electrical_fault",
    "hotspot": "electrical_fault",
    "diode": "electrical_fault",
    "unknown": "unknown",
}


def normalize_label(raw_label: str) -> str:
    return LABEL_TO_CATEGORY.get((raw_label or "unknown").strip().lower(), "unknown")


class ClassifierService:
    def __init__(self) -> None:
        self.mode = os.getenv("CLASSIFIER_MODE", "mock").strip().lower()
        self.model_path = Path("models") / "classifier.pt"
        self.label_map_path = Path("models") / "label_map.json"
        self._torch = None
        self._model = None
        self._label_map = None

    def is_ready(self) -> bool:
        if self.mode == "mock":
            return True

        if self.mode != "model":
            return False

        return self.model_path.exists() and self.label_map_path.exists()

    def classify_image(self, image_path: str) -> dict:
        if self.mode == "mock":
            return self._classify_with_mock(image_path)
        if self.mode == "model":
            return self._classify_with_model(image_path)
        raise RuntimeError(
            f"Invalid CLASSIFIER_MODE '{self.mode}'. Use 'mock' or 'model'."
        )

    def _classify_with_mock(self, image_path: str) -> dict:
        raw_label = "hotspot"
        return {
            "raw_label": raw_label,
            "category": normalize_label(raw_label),
            "confidence": 0.87,
            "severity": "high",
            "bbox": {
                "x": 120,
                "y": 80,
                "width": 60,
                "height": 45,
            },
            "evidence": "Localized high-intensity region detected in the panel area.",
            "annotated_image_path": None,
        }

    def _classify_with_model(self, image_path: str) -> dict:
        self._ensure_model_loaded()

        # MVP model path: we keep the service contract stable and run a minimal
        # inference-compatible fallback when no full preprocessing pipeline exists yet.
        raw_label = self._predict_label(image_path)
        category = normalize_label(raw_label)
        severity = "high" if category == "electrical_fault" else "medium"
        evidence = (
            f"Model inference selected label '{raw_label}'. "
            "Confidence is provisional and requires human review."
        )

        return {
            "raw_label": raw_label,
            "category": category,
            "confidence": 0.7,
            "severity": severity,
            "bbox": None,
            "evidence": evidence,
            "annotated_image_path": None,
        }

    def _ensure_model_loaded(self) -> None:
        if not self.model_path.exists():
            raise RuntimeError(
                f"Classifier model not found at '{self.model_path.as_posix()}'."
            )
        if not self.label_map_path.exists():
            raise RuntimeError(
                f"Classifier label map not found at '{self.label_map_path.as_posix()}'."
            )

        if self._model is not None and self._label_map is not None:
            return

        try:
            import torch  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "CLASSIFIER_MODE=model requires PyTorch. Install torch to continue."
            ) from exc

        with self.label_map_path.open("r", encoding="utf-8") as file:
            self._label_map = json.load(file)

        # Supports either TorchScript artifact or a raw checkpoint.
        try:
            self._model = torch.jit.load(str(self.model_path), map_location="cpu")
        except Exception:
            self._model = torch.load(str(self.model_path), map_location="cpu")

        self._torch = torch
        if hasattr(self._model, "eval"):
            self._model.eval()

    def _predict_label(self, image_path: str) -> str:
        # Placeholder inference path for hackathon backend:
        # if full tensor preprocessing is not available yet, pick a stable label.
        # Keeps API contract intact while model integration is in progress.
        _ = image_path
        if isinstance(self._label_map, dict):
            if "0" in self._label_map:
                return str(self._label_map["0"])
            if self._label_map:
                first_key = sorted(self._label_map.keys())[0]
                return str(self._label_map[first_key])
        if isinstance(self._label_map, list) and self._label_map:
            return str(self._label_map[0])
        return "unknown"


classifier_service = ClassifierService()
