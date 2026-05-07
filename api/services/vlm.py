class MockVLMService:
    def is_ready(self) -> bool:
        return False


vlm_service = MockVLMService()
