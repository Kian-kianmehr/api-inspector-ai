
from app.core.context.models import (
    APIContext,
    Endpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    RequestBody,
    BodyField,
    Response,
    ResponseField,
)

from app.core.context.validators import validate_api_context


def run_test(name, context, should_pass):
    try:
        validate_api_context(context)

        if should_pass:
            print(f"PASS: {name}")
        else:
            print(f"FAIL: {name} - Invalid data was accepted")

    except (ValueError, AttributeError, TypeError) as error:
        if should_pass:
            print(f"FAIL: {name} - {error}")
        else:
            print(f"PASS: {name}")


def create_context(endpoints=None, name="Test API",
                   base_url="https://api.example.com"):
    return APIContext(
        name=name,
        base_url=base_url,
        endpoints=endpoints or [],
    )


# 1. Valid API Context
run_test(
    "Valid API Context",
    create_context([
        Endpoint("/users", HTTPMethod.GET)
    ]),
    True,
)

# 2. Empty API name
run_test(
    "Empty API name",
    create_context(name="   "),
    False,
)

# 3. Empty Base URL
run_test(
    "Empty Base URL",
    create_context(base_url="   "),
    False,
)

# 4. Invalid URL scheme
run_test(
    "Invalid URL scheme",
    create_context(base_url="ftp://api.example.com"),
    False,
)

# 5. Missing URL host
run_test(
    "Missing URL host",
    create_context(base_url="https://"),
    False,
)

# 6. Invalid URL port
run_test(
    "Invalid URL port",
    create_context(base_url="https://api.example.com:99999"),
    False,
)

# 7. Invalid endpoint path
run_test(
    "Invalid endpoint path",
    create_context([
        Endpoint("users", HTTPMethod.GET)
    ]),
    False,
)

# 8. Invalid HTTP method
run_test(
    "Invalid HTTP method",
    create_context([
        Endpoint("/users", "INVALID")
    ]),
    False,
)

# 9. Valid parameter
run_test(
    "Valid parameter",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            parameters=[
                Parameter("page", ParameterLocation.QUERY)
            ],
        )
    ]),
    True,
)

# 10. Empty parameter name
run_test(
    "Empty parameter name",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            parameters=[
                Parameter("   ", ParameterLocation.QUERY)
            ],
        )
    ]),
    False,
)

# 11. Invalid parameter location
run_test(
    "Invalid parameter location",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            parameters=[
                Parameter("page", "INVALID")
            ],
        )
    ]),
    False,
)

# 12. Optional path parameter
run_test(
    "Optional path parameter",
    create_context([
        Endpoint(
            "/users/{user_id}",
            HTTPMethod.GET,
            parameters=[
                Parameter(
                    "user_id",
                    ParameterLocation.PATH,
                    required=False,
                )
            ],
        )
    ]),
    False,
)

# 13. Valid request body
run_test(
    "Valid request body",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.POST,
            request_body=RequestBody(
                fields=[
                    BodyField("username", "string")
                ],
            ),
        )
    ]),
    True,
)

# 14. Empty request content type
run_test(
    "Empty request content type",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.POST,
            request_body=RequestBody(content_type="   "),
        )
    ]),
    False,
)

# 15. Empty body field name
run_test(
    "Empty body field name",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.POST,
            request_body=RequestBody(
                fields=[BodyField("   ", "string")]
            ),
        )
    ]),
    False,
)

# 16. Empty body field data type
run_test(
    "Empty body field data type",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.POST,
            request_body=RequestBody(
                fields=[BodyField("username", "   ")]
            ),
        )
    ]),
    False,
)

# 17. Invalid nested body field
run_test(
    "Invalid nested body field",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.POST,
            request_body=RequestBody(
                fields=[
                    BodyField(
                        "profile",
                        "object",
                        fields=[
                            BodyField("   ", "string")
                        ],
                    )
                ],
            ),
        )
    ]),
    False,
)

# 18. Valid response
run_test(
    "Valid response",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[
                Response(
                    status_code=200,
                    fields=[
                        ResponseField("id", "integer")
                    ],
                )
            ],
        )
    ]),
    True,
)

# 19. Invalid response status code
run_test(
    "Invalid response status code",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[Response(status_code=99)],
        )
    ]),
    False,
)

# 20. Non-integer response status code
run_test(
    "Non-integer response status code",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[Response(status_code="200")],
        )
    ]),
    False,
)

# 21. Empty response content type
run_test(
    "Empty response content type",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[
                Response(status_code=200, content_type="   ")
            ],
        )
    ]),
    False,
)

# 22. Empty response field name
run_test(
    "Empty response field name",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[
                Response(
                    status_code=200,
                    fields=[ResponseField("   ", "string")],
                )
            ],
        )
    ]),
    False,
)

# 23. Empty response field data type
run_test(
    "Empty response field data type",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[
                Response(
                    status_code=200,
                    fields=[ResponseField("id", "   ")],
                )
            ],
        )
    ]),
    False,
)

# 24. Invalid nested response field
run_test(
    "Invalid nested response field",
    create_context([
        Endpoint(
            "/users",
            HTTPMethod.GET,
            responses=[
                Response(
                    status_code=200,
                    fields=[
                        ResponseField(
                            "profile",
                            "object",
                            fields=[
                                ResponseField("   ", "string")
                            ],
                        )
                    ],
                )
            ],
        )
    ]),
    False,
)
