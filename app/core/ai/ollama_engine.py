
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from socket import timeout as SocketTimeout

from app.core.ai.interface import AIInterface
from app.core.ai.models import (
    AIRequest,
    AIRequestType,
    AIResponse,
    AIFinding,
    AITestPlan,
    FindingSeverity,
)
from app.core.ai.validators import (
    validate_ai_request,
    validate_ai_response,
)
from app.core.ai.test_cases import TestCase, TestType
from app.core.context.models import APIContext


class OllamaAI(AIInterface):
    """Local Ollama engine for API test generation and result analysis."""

    ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        base_url: str = "http://localhost:11434",
        timeout: int = 180,
        temperature: float = 0.1,
    ):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model name cannot be empty")

        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("Ollama base URL cannot be empty")

        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise ValueError("Timeout must be a positive integer")

        if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
            raise ValueError("Temperature must be numeric")

        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")

        self.model = model.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = float(temperature)

    # --------------------------------------------------
    # OLLAMA COMMUNICATION
    # --------------------------------------------------

    def _generate(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
            },
        }

        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw_result = response.read().decode("utf-8")

            result = json.loads(raw_result)

        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama HTTP error {error.code}: {details}"
            ) from error

        except (URLError, SocketTimeout, TimeoutError) as error:
            raise RuntimeError(
                f"Cannot communicate with Ollama: {error}"
            ) from error

        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                "Ollama returned an invalid response"
            ) from error

        if not isinstance(result, dict):
            raise RuntimeError("Invalid Ollama response structure")

        generated_text = result.get("response")

        if not isinstance(generated_text, str) or not generated_text.strip():
            raise RuntimeError("Ollama returned an empty response")

        return generated_text

    # --------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------

    def _serialize_fields(self, fields: list) -> list:
        return [
            {
                "name": item.name,
                "data_type": item.data_type,
                "required": item.required,
                "description": item.description,
                "fields": self._serialize_fields(item.fields),
            }
            for item in fields
        ]

    def _serialize_context(self, context: APIContext) -> dict:
        if not isinstance(context, APIContext):
            raise TypeError("Invalid API context")

        endpoints = []

        for endpoint in context.endpoints:
            body = None

            if endpoint.request_body is not None:
                body = {
                    "content_type": endpoint.request_body.content_type,
                    "required": endpoint.request_body.required,
                    "description": endpoint.request_body.description,
                    "fields": self._serialize_fields(
                        endpoint.request_body.fields
                    ),
                }

            endpoints.append({
                "path": endpoint.path,
                "method": endpoint.method.value,
                "description": endpoint.description,
                "parameters": [
                    {
                        "name": parameter.name,
                        "location": parameter.location.value,
                        "required": parameter.required,
                        "description": parameter.description,
                    }
                    for parameter in endpoint.parameters
                ],
                "request_body": body,
                "responses": [
                    {
                        "status_code": response.status_code,
                        "content_type": response.content_type,
                        "description": response.description,
                        "fields": self._serialize_fields(response.fields),
                    }
                    for response in endpoint.responses
                ],
            })

        return {
            "name": context.name,
            "base_url": context.base_url,
            "description": context.description,
            "endpoints": endpoints,
        }

    # --------------------------------------------------
    # PROMPTS
    # --------------------------------------------------

    def _build_test_prompt(self, context: APIContext) -> str:
        api_data = self._serialize_context(context)

        return f"""
You are a precise API testing engineer.

Generate API test cases using only the supplied API specification.

API SPECIFICATION:
{json.dumps(api_data, ensure_ascii=False, indent=2)}

RULES:

1. Use only documented endpoints and HTTP methods.
2. Never invent parameters, fields, constraints or API behavior.
3. Never assume undocumented authentication requirements.
4. Positive tests must satisfy all documented required fields.
5. Negative tests must violate at least one documented requirement.
6. Do not invent expected HTTP status codes.
7. Use only status codes documented for the endpoint.
8. Use an empty expected_status_codes list if none are documented.
9. Do not invent boundary values or security vulnerabilities.
10. Generate edge_case or security tests only when the specification
    contains enough information to justify them.
11. Do not duplicate test scenarios.
12. Prefer a small number of reliable tests over speculative tests.
13. Use JSON-compatible values for request data.
14. Do not include explanations outside the JSON response.

OUTPUT FORMAT:

{{
    "test_cases": [
        {{
            "name": "Test name",
            "description": "Test description",
            "endpoint": "/users",
            "method": "GET",
            "test_type": "positive",
            "expected_status_codes": [],
            "headers": {{}},
            "query_params": {{}},
            "path_params": {{}},
            "request_body": null
        }}
    ]
}}

Allowed test_type values:
positive, negative, edge_case, security.

Return valid JSON only.
"""

    def _build_analysis_prompt(self, request: AIRequest) -> str:
        context_data = self._serialize_context(request.api_context)

        return f"""
You are a senior API reliability and security analyst.

Analyze API test results and produce accurate, actionable,
evidence-based findings.

API SPECIFICATION:
{json.dumps(context_data, ensure_ascii=False, indent=2)}

TEST RESULTS:
{json.dumps(request.test_results, ensure_ascii=False, indent=2)}

ADDITIONAL INSTRUCTIONS:
{request.instructions}

ANALYSIS PROCESS:

1. Examine every supplied test result.
2. Identify failed requests, unexpected status codes,
   response errors and abnormal response times.
3. Compare observed behavior with the API specification.
4. Identify the affected endpoint whenever possible.
5. Determine severity based on actual evidence.
6. Provide a concrete recommendation for every finding.
7. Provide additional useful suggestions when findings exist.

EVIDENCE RULES:

- Use only information in the API specification and test results.
- Never invent server implementation details.
- Never claim a database, authentication, network or configuration
  problem without supporting evidence.
- HTTP 500 confirms a server error but does not reveal its root cause.
- Distinguish observed facts from possible explanations.
- If the root cause is unknown, explicitly say further investigation
  is required.
- Do not report successful requests as failures.
- Do not report the same issue multiple times.
- Do not invent undocumented endpoints or parameters.
- Missing information is not proof of a defect.

FINDING REQUIREMENTS:

Every finding must contain:

- title: A short, specific issue title.
- description: Explain what happened, cite the evidence and
  describe the observable impact.
- severity: An appropriate severity level.
- endpoint: The exact documented endpoint path, when known.
- recommendation: A concrete action to investigate or resolve
  the reported issue.

IMPORTANT RECOMMENDATION RULES:

- The recommendation field MUST NOT be empty.
- Recommendations must be specific to the finding.
- Avoid vague instructions such as "Fix the issue".
- For HTTP 500, recommend checking server logs for the
  corresponding request, identifying the exception and
  inspecting the failing operation.
- Do not claim a specific dependency caused the error
  unless the supplied evidence proves it.

SEVERITY GUIDELINES:

- low: Minor issue with limited impact.
- medium: Noticeable functional or reliability issue.
- high: Significant failure affecting an API operation.
- critical: Severe or widespread impact supported by clear evidence.

SUGGESTION REQUIREMENTS:

When findings exist, provide useful and actionable suggestions.

Suggestions should:
- Be specific to the observed results.
- Complement rather than repeat finding recommendations.
- Prioritize investigation, reliability and prevention.
- Avoid assuming undocumented architecture.
- Avoid speculative security claims.

If no findings exist:
- Return an empty findings array.
- Suggestions may contain relevant improvements.
- Never invent problems.

SUMMARY REQUIREMENTS:

- Keep the summary concise and factual.
- Mention the number and general nature of detected issues.
- Never claim an unverified root cause.

OUTPUT FORMAT:

{{
    "summary": "Concise evidence-based analysis",
    "findings": [
        {{
            "title": "Specific issue title",
            "description": "Evidence and impact",
            "severity": "high",
            "endpoint": "/users",
            "recommendation": "Concrete investigation or remediation action"
        }}
    ],
    "suggestions": [
        "Actionable suggestion based on observed results"
    ]
}}

Return valid JSON only.
Do not include Markdown.
Do not include explanations outside the JSON object.
"""

    # --------------------------------------------------
    # RESPONSE PARSING
    # --------------------------------------------------

    def _parse_response(self, raw_response: str) -> dict:
        if not isinstance(raw_response, str):
            raise ValueError("AI response must be a string")

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"AI returned invalid JSON: {error}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError("AI response must be a JSON object")

        return data

    def _require_string(
        self,
        value,
        field_name: str,
        allow_empty: bool = False,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        value = value.strip()

        if not allow_empty and not value:
            raise ValueError(f"{field_name} cannot be empty")

        return value

    def _require_dict(self, value, field_name: str) -> dict:
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be an object")
        return value

    def _require_list(self, value, field_name: str) -> list:
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a list")
        return value

    # --------------------------------------------------
    # SCHEMA VALIDATION
    # --------------------------------------------------

    def _matches_data_type(self, value, data_type: str) -> bool:
        if not isinstance(data_type, str):
            return False

        data_type = data_type.lower().strip()

        if data_type in {"string", "str"}:
            return isinstance(value, str)

        if data_type in {"integer", "int"}:
            return isinstance(value, int) and not isinstance(value, bool)

        if data_type in {"number", "float"}:
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        if data_type in {"boolean", "bool"}:
            return isinstance(value, bool)

        if data_type == "object":
            return isinstance(value, dict)

        if data_type in {"array", "list"}:
            return isinstance(value, list)

        return False

    def _validate_schema_fields(
        self,
        data: dict,
        schema_fields: list,
        location: str,
        require_required: bool = False,
        allow_type_mismatch: bool = False,
    ) -> bool:
        if not isinstance(data, dict):
            raise ValueError(f"{location} must be an object")

        schema_map = {
            field.name: field
            for field in schema_fields
        }

        has_violation = False

        for name, value in data.items():
            if name not in schema_map:
                raise ValueError(
                    f"Undocumented field '{name}' in {location}"
                )

            field = schema_map[name]

            if not self._matches_data_type(value, field.data_type):
                if allow_type_mismatch:
                    has_violation = True
                    continue

                raise ValueError(
                    f"Invalid type for '{location}.{name}'. "
                    f"Expected {field.data_type}"
                )

            if field.fields:
                if field.data_type.lower().strip() != "object":
                    raise ValueError(
                        f"Nested fields for '{name}' require object type"
                    )

                nested_violation = self._validate_schema_fields(
                    value,
                    field.fields,
                    f"{location}.{name}",
                    require_required=require_required,
                    allow_type_mismatch=allow_type_mismatch,
                )

                has_violation = has_violation or nested_violation

        if require_required:
            for field in schema_fields:
                if field.required and field.name not in data:
                    raise ValueError(
                        f"Missing required field '{location}.{field.name}'"
                    )

        return has_violation

    # --------------------------------------------------
    # PARAMETER VALIDATION
    # --------------------------------------------------

    def _parameter_map(self, endpoint, location: str) -> dict:
        return {
            parameter.name: parameter
            for parameter in endpoint.parameters
            if parameter.location.value == location
        }

    def _validate_parameters(
        self,
        values: dict,
        endpoint,
        location: str,
    ) -> bool:
        parameters = self._parameter_map(endpoint, location)

        normalized = {
            name.lower() if location == "header" else name: parameter
            for name, parameter in parameters.items()
        }

        provided = set()

        for name, value in values.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"Invalid {location} parameter name")

            lookup_name = name.lower() if location == "header" else name

            if lookup_name not in normalized:
                raise ValueError(
                    f"Undocumented {location} parameter: {name}"
                )

            if (
                not isinstance(value, (str, int, float, bool))
                or value is None
            ):
                raise ValueError(
                    f"{location} parameter '{name}' must be a scalar value"
                )

            provided.add(lookup_name)

        return any(
            parameter.required and name not in provided
            for name, parameter in normalized.items()
        )

    # --------------------------------------------------
    # REQUEST BODY VALIDATION
    # --------------------------------------------------

    def _validate_request_body(
        self,
        request_body,
        endpoint,
        test_type: TestType,
    ) -> bool:
        body_schema = endpoint.request_body

        if request_body is None:
            if body_schema is None:
                return False

            if body_schema.required:
                if test_type == TestType.NEGATIVE:
                    return True

                raise ValueError("Required request body is missing")

            return False

        if body_schema is None:
            raise ValueError("Request body is not documented")

        if not body_schema.fields:
            raise ValueError("Request body schema is incomplete")

        return self._validate_schema_fields(
            request_body,
            body_schema.fields,
            "request_body",
            require_required=(test_type == TestType.POSITIVE),
            allow_type_mismatch=(test_type == TestType.NEGATIVE),
        )

    # --------------------------------------------------
    # TEST CASE VALIDATION
    # --------------------------------------------------

    def _validate_test_case(
        self,
        item: dict,
        context: APIContext,
        index: int,
    ) -> TestCase:
        if not isinstance(item, dict):
            raise ValueError(f"Test case #{index} must be an object")

        name = self._require_string(item.get("name"), "name")
        description = self._require_string(
            item.get("description"),
            "description",
        )
        endpoint_path = self._require_string(
            item.get("endpoint"),
            "endpoint",
        )
        method = self._require_string(
            item.get("method"),
            "method",
        ).upper()

        endpoint = next(
            (
                candidate
                for candidate in context.endpoints
                if candidate.path == endpoint_path
                and candidate.method.value == method
            ),
            None,
        )

        if endpoint is None:
            raise ValueError(
                f"Unknown endpoint: {method} {endpoint_path}"
            )

        try:
            test_type = TestType(item.get("test_type"))
        except (ValueError, TypeError) as error:
            raise ValueError("Invalid test type") from error

        headers = self._require_dict(item.get("headers", {}), "headers")
        query_params = self._require_dict(
            item.get("query_params", {}),
            "query_params",
        )
        path_params = self._require_dict(
            item.get("path_params", {}),
            "path_params",
        )

        request_body = item.get("request_body")

        if request_body is not None and not isinstance(request_body, dict):
            raise ValueError("request_body must be an object or null")

        expected_status_codes = self._require_list(
            item.get("expected_status_codes", []),
            "expected_status_codes",
        )

        documented_status_codes = {
            response.status_code
            for response in endpoint.responses
        }

        validated_status_codes = []

        for code in expected_status_codes:
            if (
                not isinstance(code, int)
                or isinstance(code, bool)
                or not 100 <= code <= 599
            ):
                raise ValueError(f"Invalid HTTP status code: {code}")

            if code not in documented_status_codes:
                raise ValueError(f"Undocumented status code: {code}")

            if code not in validated_status_codes:
                validated_status_codes.append(code)

        if test_type in {TestType.EDGE_CASE, TestType.SECURITY}:
            raise ValueError(
                f"Cannot validate {test_type.value} test: "
                "the current API context does not contain sufficient "
                "boundary or security metadata"
            )

        missing_required_parameter = False

        for location, values in (
            ("header", headers),
            ("query", query_params),
            ("path", path_params),
        ):
            missing = self._validate_parameters(
                values,
                endpoint,
                location,
            )
            missing_required_parameter |= missing

        cookie_parameters = self._parameter_map(endpoint, "cookie")

        if any(
            parameter.required
            for parameter in cookie_parameters.values()
        ):
            raise ValueError(
                "Required cookie parameters cannot be represented "
                "by the current TestCase model"
            )

        if test_type == TestType.POSITIVE and missing_required_parameter:
            raise ValueError(
                "Positive test is missing a required parameter"
            )

        body_violation = self._validate_request_body(
            request_body,
            endpoint,
            test_type,
        )

        if test_type == TestType.NEGATIVE:
            if not (missing_required_parameter or body_violation):
                raise ValueError(
                    "Negative test does not violate a documented requirement"
                )

        return TestCase(
            name=name,
            description=description,
            endpoint=endpoint_path,
            method=method,
            test_type=test_type,
            expected_status_codes=validated_status_codes,
            headers=headers,
            query_params=query_params,
            path_params=path_params,
            request_body=request_body,
        )

    # --------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------

    def _deduplicate_test_cases(
        self,
        test_cases: list[TestCase],
    ) -> list[TestCase]:
        unique_cases = []
        seen = set()

        for test_case in test_cases:
            signature = {
                "endpoint": test_case.endpoint,
                "method": test_case.method,
                "test_type": test_case.test_type.value,
                "expected_status_codes": sorted(
                    test_case.expected_status_codes
                ),
                "headers": test_case.headers,
                "query_params": test_case.query_params,
                "path_params": test_case.path_params,
                "request_body": test_case.request_body,
            }

            fingerprint = json.dumps(
                signature,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_cases.append(test_case)

        return unique_cases

    # --------------------------------------------------
    # TEST PLAN SUMMARY
    # --------------------------------------------------

    def _build_summary(self, test_cases: list[TestCase]) -> str:
        counts = {test_type.value: 0 for test_type in TestType}

        for test_case in test_cases:
            counts[test_case.test_type.value] += 1

        return (
            f"Validated {len(test_cases)} test cases: "
            f"{counts['positive']} positive, "
            f"{counts['negative']} negative, "
            f"{counts['edge_case']} edge-case, "
            f"{counts['security']} security."
        )

    # --------------------------------------------------
    # TEST GENERATION
    # --------------------------------------------------

    def generate_tests(self, request: AIRequest) -> AITestPlan:
        validate_ai_request(request)

        if request.request_type != AIRequestType.TEST_GENERATION:
            raise ValueError(
                "generate_tests requires a TEST_GENERATION request"
            )

        if not isinstance(request.api_context, APIContext):
            raise TypeError("AIRequest contains invalid API context")

        if not request.api_context.endpoints:
            raise ValueError("API context contains no endpoints")

        prompt = self._build_test_prompt(request.api_context)

        if request.instructions:
            instructions = self._require_string(
                request.instructions,
                "instructions",
            )
            prompt += f"\nADDITIONAL INSTRUCTIONS:\n{instructions}"

        raw_response = self._generate(prompt)
        data = self._parse_response(raw_response)

        raw_cases = self._require_list(
            data.get("test_cases"),
            "test_cases",
        )

        valid_cases = []
        rejected_cases = []

        for index, item in enumerate(raw_cases, start=1):
            try:
                valid_cases.append(
                    self._validate_test_case(
                        item,
                        request.api_context,
                        index,
                    )
                )
            except (ValueError, TypeError, KeyError) as error:
                rejected_cases.append(
                    f"Test case #{index}: {error}"
                )

        unique_cases = self._deduplicate_test_cases(valid_cases)

        if not unique_cases:
            details = (
                "\n".join(rejected_cases)
                if rejected_cases
                else "The model returned no test cases."
            )

            raise ValueError(
                "No valid test cases were generated.\n"
                f"Rejected cases:\n{details}"
            )

        return AITestPlan(
            summary=self._build_summary(unique_cases),
            test_cases=unique_cases,
        )

    # --------------------------------------------------
    # FINDING VALIDATION
    # --------------------------------------------------

    def _validate_finding(
        self,
        item: dict,
        context: APIContext,
        index: int,
    ) -> AIFinding:
        if not isinstance(item, dict):
            raise ValueError(f"Finding #{index} must be an object")

        title = self._require_string(
            item.get("title"),
            f"finding[{index}].title",
        )
        description = self._require_string(
            item.get("description"),
            f"finding[{index}].description",
        )
        severity = self._require_string(
            item.get("severity"),
            f"finding[{index}].severity",
        ).lower()

        try:
            severity = FindingSeverity(severity)
        except ValueError as error:
            raise ValueError(
                f"Invalid severity in finding #{index}"
            ) from error

        endpoint_path = item.get("endpoint", "")

        if endpoint_path:
            endpoint_path = self._require_string(
                endpoint_path,
                f"finding[{index}].endpoint",
            )

            known_paths = {
                endpoint.path
                for endpoint in context.endpoints
            }

            if endpoint_path not in known_paths:
                raise ValueError(
                    f"Finding #{index} references unknown endpoint"
                )

        recommendation = self._require_string(
            item.get("recommendation"),
            f"finding[{index}].recommendation",
        )

        return AIFinding(
            title=title,
            description=description,
            severity=severity,
            endpoint=endpoint_path,
            recommendation=recommendation,
        )

    # --------------------------------------------------
    # RESULT ANALYSIS
    # --------------------------------------------------

    def analyze_results(self, request: AIRequest) -> AIResponse:
        validate_ai_request(request)

        if request.request_type != AIRequestType.RESULT_ANALYSIS:
            raise ValueError(
                "analyze_results requires a RESULT_ANALYSIS request"
            )

        if not isinstance(request.api_context, APIContext):
            raise TypeError("AIRequest contains invalid API context")

        prompt = self._build_analysis_prompt(request)
        raw_response = self._generate(prompt)
        data = self._parse_response(raw_response)

        summary = self._require_string(
            data.get("summary"),
            "summary",
        )

        raw_findings = self._require_list(
            data.get("findings", []),
            "findings",
        )
        raw_suggestions = self._require_list(
            data.get("suggestions", []),
            "suggestions",
        )

        findings = [
            self._validate_finding(
                item,
                request.api_context,
                index,
            )
            for index, item in enumerate(raw_findings, start=1)
        ]

        suggestions = [
            self._require_string(
                suggestion,
                f"suggestions[{index}]",
            )
            for index, suggestion in enumerate(
                raw_suggestions,
                start=1,
            )
        ]

        response = AIResponse(
            request_type=request.request_type,
            summary=summary,
            findings=findings,
            suggestions=suggestions,
        )
        validate_ai_response(response)
        return response
