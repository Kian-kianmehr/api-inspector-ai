from abc import ABC, abstractmethod

from app.core.ai.models import AIRequest, AIResponse, AITestPlan


class AIInterface(ABC):

    @abstractmethod
    def generate_tests(self, request: AIRequest) -> AITestPlan:
        pass

    @abstractmethod
    def analyze_results(self, request: AIRequest) -> AIResponse:
        pass