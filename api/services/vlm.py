import json
import os

import httpx


class VLMService:
    def __init__(self) -> None:
        self.mode = os.getenv("VLM_MODE", "mock").strip().lower()
        self.api_url = os.getenv(
            "VLM_API_URL",
            "http://localhost:8001/v1/chat/completions",
        ).strip()
        self.model_name = os.getenv("VLM_MODEL_NAME", "qwen2.5-vl-7b")
        self.timeout_seconds = float(os.getenv("VLM_TIMEOUT_SECONDS", "20"))

    def is_ready(self) -> bool:
        if self.mode == "mock":
            return True
        if self.mode == "api":
            return bool(self.api_url)
        return False

    def explain_finding(self, image_path: str, classifier_result: dict) -> dict:
        if self.mode == "mock":
            return self._explain_with_mock(image_path, classifier_result)
        if self.mode == "api":
            return self._explain_with_vlm(image_path, classifier_result)
        return self._fallback_response(
            reason=f"Invalid VLM_MODE '{self.mode}'. Use 'mock' or 'api'.",
            classifier_result=classifier_result,
        )

    def _explain_with_mock(self, image_path: str, classifier_result: dict) -> dict:
        _ = image_path, classifier_result
        return {
            "explanation": (
                "The image may show a localized thermal anomaly compatible with "
                "a possible hotspot or electrical imbalance."
            ),
            "recommended_action": (
                "Prioritize human review and inspect electrical connections or affected string."
            ),
            "uncertainty": "AI-assisted triage only. Human review is required.",
        }

    def _explain_with_vlm(self, image_path: str, classifier_result: dict) -> dict:
        prompt = self._build_prompt(image_path, classifier_result)
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant for photovoltaic inspection triage. "
                        "Never provide definitive technical diagnosis. "
                        "Always reinforce that human review is required."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(self.api_url, json=payload)
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]
            parsed = self._parse_vlm_json(content)
            return self._normalize_response(parsed)
        except Exception as exc:
            return self._fallback_response(str(exc), classifier_result)

    def _build_prompt(self, image_path: str, classifier_result: dict) -> str:
        return (
            "Analyze this photovoltaic inspection finding and return JSON only.\n"
            f"image_path: {image_path}\n"
            f"classifier_result: {json.dumps(classifier_result)}\n\n"
            "Return exactly this JSON schema:\n"
            "{\n"
            '  "explanation": "...",\n'
            '  "recommended_action": "...",\n'
            '  "uncertainty": "..."\n'
            "}\n\n"
            "Rules:\n"
            "- Do not provide definitive diagnosis.\n"
            "- Keep content concise and useful for triage.\n"
            "- Always reinforce that human review is required.\n"
        )

    def _parse_vlm_json(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        return json.loads(text)

    def _normalize_response(self, parsed: dict) -> dict:
        explanation = str(parsed.get("explanation", "")).strip()
        recommended_action = str(parsed.get("recommended_action", "")).strip()
        uncertainty = str(parsed.get("uncertainty", "")).strip()

        if not uncertainty:
            uncertainty = "AI-assisted triage only. Human review is required."
        elif "human review" not in uncertainty.lower():
            uncertainty = f"{uncertainty} Human review is required."

        if not explanation:
            explanation = (
                "Potential anomaly identified by AI-assisted triage. "
                "Assessment is preliminary and requires human review."
            )
        if not recommended_action:
            recommended_action = (
                "Prioritize human review and inspect related panel components."
            )

        return {
            "explanation": explanation,
            "recommended_action": recommended_action,
            "uncertainty": uncertainty,
        }

    def _fallback_response(self, reason: str, classifier_result: dict) -> dict:
        category = classifier_result.get("category", "unknown")
        severity = classifier_result.get("severity", "unknown")
        return {
            "explanation": (
                f"Automated explanation was unavailable. Classifier flagged "
                f"category '{category}' with severity '{severity}'. "
                "Use this as triage signal only."
            ),
            "recommended_action": (
                "Proceed with human review before any operational decision."
            ),
            "uncertainty": (
                "AI-assisted triage only. Human review is required. "
                f"Fallback reason: {reason}"
            ),
        }


vlm_service = VLMService()
