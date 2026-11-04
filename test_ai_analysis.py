import json

import pytest

from app.core.ai.models import (
    AIRequest,
    AIRequestType,
    FindingSeverity,
)
from app.core.ai.ollama_engine import OllamaAI
from app.core.context.models import APIContext, Endpoint, HTTPMethod, Response


@pytest.fixture
def api_context():
    return APIContext(
        name="User API",
        base_url="https://api.example.com",
        description="API for managing users",
        endpoints=[
            Endpoint(
                path="/users",
                method=HTTPMethod.GET,
                description="Get all users",
            )
        ],
    )


@pytest.fixture
def analysis_request(api_context):
    return AIRequest(
        request_type=AIRequestType.RESULT_ANALYSIS,
        api_context=api_context,
        test_results=[
            {
                "endpoint": "/users",
                "method": "GET",
                "status": "failed",
                "status_code": 500,
                "expected_status_codes": [200],
                "error": "Internal Server Error",
            }
        ],
    )


def mock_model_response(monkeypatch, ai, response):
    monkeypatch.setattr(
        ai,
        "_generate",
        lambda prompt: json.dumps(response),
    )


def test_analyze_results_returns_validated_finding(
    monkeypatch,
    analysis_request,
):
    ai = OllamaAI()
    mock_model_response(
        monkeypatch,
        ai,
        {
            "summary": "The GET /users request returned an unexpected server error.",
            "findings": [
                {
                    "title": "Unexpected server error",
                    "description": "GET /users returned HTTP 500 while HTTP 200 was expected.",
                    "severity": "high",
                    "endpoint": "/users",
                    "recommendation": "Investigate the server-side error.",
                }
            ],
            "suggestions": ["Inspect the server logs for this request."],
        },
    )

    response = ai.analyze_results(analysis_request)

    assert response.request_type == AIRequestType.RESULT_ANALYSIS
    assert response.summary
    assert len(response.findings) == 1
    assert response.findings[0].severity == FindingSeverity.HIGH
    assert response.findings[0].endpoint == "/users"
    assert response.suggestions == ["Inspect the server logs for this request."]


def test_analyze_results_accepts_no_findings(
    monkeypatch,
    analysis_request,
):
    ai = OllamaAI()
    mock_model_response(
        monkeypatch,
        ai,
        {
            "summary": "No issues were identified in the supplied results.",
            "findings": [],
            "suggestions": [],
        },
    )

    response = ai.analyze_results(analysis_request)

    assert response.findings == []
    assert response.suggestions == []


def test_analyze_results_rejects_invalid_severity(
    monkeypatch,
    analysis_request,
):
    ai = OllamaAI()
    mock_model_response(
        monkeypatch,
        ai,
        {
            "summary": "An issue was found.",
            "findings": [
                {
                    "title": "Unexpected response",
                    "description": "The endpoint returned an unexpected response.",
                    "severity": "urgent",
                    "endpoint": "/users",
                    "recommendation": "Investigate the response.",
                }
            ],
            "suggestions": [],
        },
    )

    with pytest.raises(ValueError, match="Invalid severity"):
        ai.analyze_results(analysis_request)


def test_analyze_results_rejects_unknown_endpoint(
    monkeypatch,
    analysis_request,
):
    ai = OllamaAI()
    mock_model_response(
        monkeypatch,
        ai,
        {
            "summary": "An issue was found.",
            "findings": [
                {
                    "title": "Unknown endpoint finding",
                    "description": "The result references an unknown endpoint.",
                    "severity": "medium",
                    "endpoint": "/admin",
                    "recommendation": "Verify the endpoint.",
                }
            ],
            "suggestions": [],
        },
    )

    with pytest.raises(ValueError, match="unknown endpoint"):
        ai.analyze_results(analysis_request)


def test_analyze_results_rejects_invalid_json(
    monkeypatch,
    analysis_request,
):
    ai = OllamaAI()
    monkeypatch.setattr(ai, "_generate", lambda prompt: "not valid json")

    with pytest.raises(ValueError, match="invalid JSON"):
        ai.analyze_results(analysis_request)


def test_analyze_results_requires_test_results(api_context):
    ai = OllamaAI()
    request = AIRequest(
        request_type=AIRequestType.RESULT_ANALYSIS,
        api_context=api_context,
        test_results=[],
    )

    with pytest.raises(ValueError, match="Test results are required"):
        ai.analyze_results(request)


def test_analyze_results_rejects_wrong_request_type(
    api_context,
):
    ai = OllamaAI()
    request = AIRequest(
        request_type=AIRequestType.TEST_GENERATION,
        api_context=api_context,
        test_results=[{"status": "failed"}],
    )

    with pytest.raises(ValueError, match="RESULT_ANALYSIS"):
        ai.analyze_results(request)


def test_analysis_prompt_contains_supplied_results(analysis_request):
    ai = OllamaAI()

    prompt = ai._build_analysis_prompt(analysis_request)

    assert '"status_code": 500' in prompt
    assert '"expected_status_codes": [\n      200\n    ]' in prompt
    assert "Internal Server Error" in prompt


def build_live_context():
    return APIContext(
        name="User API",
        base_url="https://api.example.com",
        description="API for managing users",
        endpoints=[
            Endpoint(
                path="/users",
                method=HTTPMethod.GET,
                description="Return a paginated list of users.",
                responses=[
                    Response(
                        status_code=200,
                        description="Users returned successfully.",
                    ),
                ],
            )
        ],
    )


def print_analysis(label, response):
    print("\n" + "=" * 50)
    print(label)
    print("=" * 50)
    print("SUMMARY")
    print(response.summary)
    print(f"\nFINDINGS ({len(response.findings)})")

    for index, finding in enumerate(response.findings, start=1):
        print(f"[{index}] {finding.title}")
        print(f"Severity: {finding.severity.value}")
        print(f"Endpoint: {finding.endpoint}")
        print(f"Description: {finding.description}")
        print(f"Recommendation: {finding.recommendation}")

    print("\nSUGGESTIONS")
    if response.suggestions:
        for suggestion in response.suggestions:
            print(f"- {suggestion}")
    else:
        print("No additional suggestions.")


def main():
    """Run failure and success analyses against the local Ollama model."""
    context = build_live_context()
    ai = OllamaAI()

    scenarios = [
        (
            "FAILED TEST: unexpected HTTP 500",
            [
                {
                    "test_name": "List users - server error",
                    "endpoint": "/users",
                    "method": "GET",
                    "status": "failed",
                    "status_code": 500,
                    "expected_status_codes": [200],
                    "response_time_ms": 125,
                    "response_body": {"detail": "Internal Server Error"},
                    "error": "Unexpected HTTP status code: 500",
                }
            ],
            "Identify only issues directly supported by these results. "
            "Do not infer a root cause that is not shown by the evidence.",
        ),
        (
            "SUCCESSFUL TEST: expected HTTP 200",
            [
                {
                    "test_name": "List users - successful response",
                    "endpoint": "/users",
                    "method": "GET",
                    "status": "passed",
                    "status_code": 200,
                    "expected_status_codes": [200],
                    "response_time_ms": 125,
                    "response_body": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"},
                    ],
                    "error": None,
                }
            ],
            "Report only issues directly supported by these results. "
            "If no issue is demonstrated, return an empty findings list. "
            "Do not invent vulnerabilities or problems.",
        ),
    ]

    for label, test_results, instructions in scenarios:
        request = AIRequest(
            request_type=AIRequestType.RESULT_ANALYSIS,
            api_context=context,
            test_results=test_results,
            instructions=instructions,
        )
        print(f"\nAnalyzing scenario: {label}")
        response = ai.analyze_results(request)
        print_analysis(label, response)


if __name__ == "__main__":
    main()
