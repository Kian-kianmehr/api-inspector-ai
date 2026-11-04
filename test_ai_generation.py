
from app.core.ai.ollama_engine import OllamaAI
from app.core.ai.models import AIRequest, AIRequestType
from app.core.context.models import (
    APIContext,
    Endpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation
)


def main():
    # Define a sample API context
    context = APIContext(
        name="User API",
        base_url="https://api.example.com",
        description="API for managing users",
        endpoints=[
            Endpoint(
                path="/users",
                method=HTTPMethod.GET,
                description="Get all users",
                parameters=[
                    Parameter(
                        name="page",
                        location=ParameterLocation.QUERY,
                        required=False,
                        description="Page number"
                    )
                ]
            ),
            Endpoint(
                path="/users",
                method=HTTPMethod.POST,
                description="Create a new user"
            )
        ]
    )

    # Create an AI request
    ai_request = AIRequest(
        request_type=AIRequestType.TEST_GENERATION,
        api_context=context,
        instructions=(
            "Generate a balanced set of positive, negative, "
            "and edge-case tests. Avoid duplicate test cases."
        )
    )

    # Initialize Ollama
    ai = OllamaAI()

    # Generate test plan
    print("Generating test plan with Qwen...\n")

    plan = ai.generate_tests(ai_request)

    # Display summary
    print("=" * 50)
    print("TEST PLAN SUMMARY")
    print("=" * 50)
    print(plan.summary)

    # Display generated test cases
    print("\n" + "=" * 50)
    print(f"GENERATED TEST CASES ({len(plan.test_cases)})")
    print("=" * 50)

    for index, test_case in enumerate(plan.test_cases, start=1):
        print(f"\n[{index}] {test_case.name}")
        print(f"Description: {test_case.description}")
        print(f"Endpoint: {test_case.method} {test_case.endpoint}")
        print(f"Type: {test_case.test_type.value}")
        print(
            f"Expected status codes: "
            f"{test_case.expected_status_codes}"
        )
        print(f"Headers: {test_case.headers}")
        print(f"Query params: {test_case.query_params}")
        print(f"Path params: {test_case.path_params}")
        print(f"Request body: {test_case.request_body}")


if __name__ == "__main__":
    main()
