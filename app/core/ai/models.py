from dataclasses import dataclass, field
from enum import Enum
from app.core.context.models import APIContext


class AIRequestType(str,Enum):
    TEST_GENERATION = "test_generation"
    RESULT_ANALYSIS = "result_analysis"


@dataclass
class AIRequest:
    request_type: AIRequestType
    api_context: APIContext
    test_results: list[dict]=field(default_factory=list)
    instructions: str = ""

@dataclass
class AIFinding:
    title: str
    description: str
    severity: str
    endpoint: str=""
    recommendation: str = ""


@dataclass
class AIResponse:
    request_type: AIRequestType
    summary: str
    findings: list[AIFinding] = field(default_factory=list)
    suggestions: list[str]=field(default_factory=list)