class MockClassifierService:
    def is_ready(self) -> bool:
        return False


classifier_service = MockClassifierService()
