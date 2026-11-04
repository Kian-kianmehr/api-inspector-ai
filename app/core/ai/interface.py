from abc import ABC, abstractmethod
from app.core.ai.models import AIRequest, AIResponse


class AIInterface(ABC):

    @abstractmethod
    def generate_tests(self, request: AIRequest) -> AIResponse:
        pass

    @abstractmethod
    def analyze_results(self, request: AIRequest) -> AIResponse:
        pass