from dataclasses import dataclass, field
from enum import Enum


class TestType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE_CASE = "edge_case"
    SECURITY = "security"


@dataclass
class TestCase:
    name: str
    description: str
    endpoint: str
    method: str
    test_type: TestType
    expected_status_codes: list[int] = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    path_params: dict = field(default_factory=dict)
    request_body: dict | None = None