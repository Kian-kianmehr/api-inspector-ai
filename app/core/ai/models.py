from dataclasses import dataclass, field
from enum import Enum
from app.core.context.models import APIContext
from app.core.ai.test_cases import TestCase

class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIRequestType(str, Enum):
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



@dataclass
class AITestPlan:
    summary: str
    test_cases: list[TestCase] = field(default_factory=list)