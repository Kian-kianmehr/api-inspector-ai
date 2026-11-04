
from app.core.ai.models import (
    AIRequest,
    AIResponse,
    AIFinding,
    AIRequestType,
    FindingSeverity,
)

from app.core.context.models import APIContext
from app.core.context.validators import validate_api_context


def validate_ai_request(request: AIRequest) -> None:
    if not isinstance(request, AIRequest):
        raise ValueError("Invalid AI request.")

    if not isinstance(request.request_type, AIRequestType):
        raise ValueError("Invalid request type.")

    if not isinstance(request.api_context, APIContext):
        raise ValueError("Invalid API context.")

    validate_api_context(request.api_context)

    if not isinstance(request.test_results, list):
        raise ValueError("Test results must be a list.")

    for result in request.test_results:
        if not isinstance(result, dict):
            raise ValueError("Each test result must be a dictionary.")

    if request.request_type == AIRequestType.RESULT_ANALYSIS:
        if not request.test_results:
            raise ValueError("Test results are required for result analysis.")

    if not isinstance(request.instructions, str):
        raise ValueError("Instructions must be a string.")


def validate_ai_finding(finding: AIFinding) -> None:
    if not isinstance(finding, AIFinding):
        raise ValueError("Invalid AI finding.")

    if not isinstance(finding.title, str) or not finding.title.strip():
        raise ValueError("Finding title cannot be empty.")

    if not isinstance(finding.description, str) or not finding.description.strip():
        raise ValueError("Finding description cannot be empty.")

    if not isinstance(finding.severity, FindingSeverity):
        raise ValueError("Invalid finding severity.")

    if not isinstance(finding.endpoint, str):
        raise ValueError("Finding endpoint must be a string.")

    if not isinstance(finding.recommendation, str):
        raise ValueError("Finding recommendation must be a string.")


def validate_ai_response(response: AIResponse) -> None:
    if not isinstance(response, AIResponse):
        raise ValueError("Invalid AI response.")

    if not isinstance(response.request_type, AIRequestType):
        raise ValueError("Invalid response request type.")

    if not isinstance(response.summary, str) or not response.summary.strip():
        raise ValueError("Response summary cannot be empty.")

    if not isinstance(response.findings, list):
        raise ValueError("Findings must be a list.")

    for finding in response.findings:
        validate_ai_finding(finding)

    if not isinstance(response.suggestions, list):
        raise ValueError("Suggestions must be a list.")

    for suggestion in response.suggestions:
        if not isinstance(suggestion, str) or not suggestion.strip():
            raise ValueError("Each suggestion must be a non-empty string.")
