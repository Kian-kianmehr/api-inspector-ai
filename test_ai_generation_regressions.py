import json

import pytest

from app.core.ai.models import AIRequest, AIRequestType
from app.core.ai.ollama_engine import OllamaAI
from app.core.context.models import (
    APIContext,
    BodyField,
    Endpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
)


def test_generation_infers_only_documented_status_codes(monkeypatch):
    context = APIContext(
        name="Todo API",
        base_url="https://api.example.com",
        endpoints=[
            Endpoint(
                path="/todos",
                method=HTTPMethod.GET,
                responses=[Response(status_code=200)],
            ),
            Endpoint(
                path="/todos",
                method=HTTPMethod.POST,
                request_body=RequestBody(
                    required=True,
                    fields=[
                        BodyField(name="title", data_type="string", required=True),
                        BodyField(name="completed", data_type="boolean"),
                    ],
                ),
                responses=[
                    Response(status_code=201),
                    Response(status_code=400),
                ],
            ),
        ],
    )
    ai = OllamaAI()
    model_output = {
        "test_cases": [
            {
                "name": "Get todos successfully",
                "description": "Retrieve all todos.",
                "endpoint": "/todos",
                "method": "GET",
                "test_type": "positive",
                "expected_status_codes": [],
                "headers": {},
                "query_params": {},
                "path_params": {},
                "request_body": None,
            },
            {
                "name": "Create todo without title",
                "description": "Omit the required title field.",
                "endpoint": "/todos",
                "method": "POST",
                "test_type": "negative",
                "expected_status_codes": [],
                "headers": {},
                "query_params": {},
                "path_params": {},
                "request_body": {"completed": False},
            },
        ]
    }
    monkeypatch.setattr(ai, "_generate", lambda prompt: json.dumps(model_output))

    plan = ai.generate_tests(
        AIRequest(
            request_type=AIRequestType.TEST_GENERATION,
            api_context=context,
        )
    )

    assert len(plan.test_cases) == 2
    assert plan.test_cases[0].expected_status_codes == [200]
    assert plan.test_cases[1].expected_status_codes == [400]


def test_generation_rejects_negative_case_with_missing_path_parameter():
    context = APIContext(
        name="Todo API",
        base_url="https://api.example.com",
        endpoints=[
            Endpoint(
                path="/todos/{id}",
                method=HTTPMethod.GET,
                parameters=[
                    Parameter(
                        name="id",
                        location=ParameterLocation.PATH,
                        required=True,
                    )
                ],
                responses=[
                    Response(status_code=200),
                    Response(status_code=404),
                ],
            )
        ],
    )
    ai = OllamaAI()

    with pytest.raises(ValueError, match="endpoint URL would not be executable"):
        ai._validate_test_case(
            {
                "name": "Get todo without ID",
                "description": "Omit the required path parameter.",
                "endpoint": "/todos/{id}",
                "method": "GET",
                "test_type": "negative",
                "expected_status_codes": [404],
                "headers": {},
                "query_params": {},
                "path_params": {},
                "request_body": None,
            },
            context,
            1,
        )
