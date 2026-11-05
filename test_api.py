from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import ai as ai_routes

from app.core.ai.models import (
    AITestPlan,
    AIRequestType,
    AIResponse,
    AIFinding,
    FindingSeverity,
)
from app.core.ai.test_cases import TestCase, TestType


client = TestClient(app)


def sample_api_context():
    return {
        "name": "Users API",
        "base_url": "https://example.com",
        "endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "description": "Retrieve users",
            }
        ],
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "api-inspector-ai",
    }


def test_test_generation(monkeypatch):
    captured = {}

    def mock_generate_tests(request):
        captured["request"] = request

        return AITestPlan(
            summary="Test plan generated successfully",
            test_cases=[
                TestCase(
                    name="Get users",
                    description="Check retrieving users",
                    endpoint="/users",
                    method="GET",
                    test_type=TestType.POSITIVE,
                    expected_status_codes=[200],
                )
            ],
        )

    monkeypatch.setattr(
        ai_routes.engine,
        "generate_tests",
        mock_generate_tests,
    )

    payload = {
        "api_context": sample_api_context(),
        "instructions": "Generate basic tests",
    }

    response = client.post(
        "/v1/test-generation",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"] == "Test plan generated successfully"
    assert len(data["test_cases"]) == 1
    assert data["test_cases"][0]["name"] == "Get users"
    assert data["test_cases"][0]["test_type"] == "positive"

    assert captured["request"].request_type == AIRequestType.TEST_GENERATION
    assert captured["request"].api_context.name == "Users API"


def test_result_analysis(monkeypatch):
    captured = {}

    def mock_analyze_results(request):
        captured["request"] = request

        return AIResponse(
            request_type=AIRequestType.RESULT_ANALYSIS,
            summary="One issue was detected in the API.",
            findings=[
                AIFinding(
                    title="Server Error",
                    description="The endpoint returned HTTP 500.",
                    severity=FindingSeverity.HIGH,
                    endpoint="/users",
                    recommendation="Investigate the server error.",
                )
            ],
            suggestions=[
                "Improve error handling."
            ],
        )

    monkeypatch.setattr(
        ai_routes.engine,
        "analyze_results",
        mock_analyze_results,
    )

    payload = {
        "api_context": sample_api_context(),
        "test_results": [
            {
                "endpoint": "/users",
                "method": "GET",
                "status_code": 500,
                "success": False,
            }
        ],
        "instructions": "Analyze the failed request.",
    }

    response = client.post(
        "/v1/result-analysis",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_type"] == "result_analysis"
    assert data["summary"] == "One issue was detected in the API."
    assert len(data["findings"]) == 1

    assert data["findings"][0]["title"] == "Server Error"
    assert data["findings"][0]["severity"] == "high"
    assert data["findings"][0]["endpoint"] == "/users"

    assert len(data["suggestions"]) == 1

    assert captured["request"].request_type == AIRequestType.RESULT_ANALYSIS
    assert captured["request"].api_context.name == "Users API"
    assert len(captured["request"].test_results) == 1