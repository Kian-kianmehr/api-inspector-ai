
from urllib.parse import urlparse

from app.core.context.models import (
    APIContext,
    HTTPMethod,
    ParameterLocation,
)


def validate_fields(fields, field_type):
    for item in fields:
        if not item.name.strip():
            raise ValueError(f"{field_type} field name cannot be empty")

        if not item.data_type.strip():
            raise ValueError(
                f"{field_type} field data type cannot be empty: {item.name}"
            )

        validate_fields(item.fields, field_type)


def validate_api_context(context: APIContext):

    # Validate API context
    if not context.name.strip():
        raise ValueError("API name cannot be empty")

    if not context.base_url.strip():
        raise ValueError("API base URL cannot be empty")

    parsed_url = urlparse(context.base_url)

    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("API base URL must use HTTP or HTTPS")

    if not parsed_url.hostname:
        raise ValueError("API base URL must contain a valid host")

    try:
        if parsed_url.port is not None and not 1 <= parsed_url.port <= 65535:
            raise ValueError("Invalid API base URL port")
    except ValueError as error:
        raise ValueError("Invalid API base URL port") from error

    # Validate endpoints
    for endpoint in context.endpoints:

        if not endpoint.path.startswith("/"):
            raise ValueError(
                f"Endpoint path must start with '/': {endpoint.path}"
            )

        if not isinstance(endpoint.method, HTTPMethod):
            raise ValueError(
                f"Invalid HTTP method: {endpoint.method}"
            )

        # Validate parameters
        for parameter in endpoint.parameters:

            if not parameter.name.strip():
                raise ValueError("Parameter name cannot be empty")

            if not isinstance(parameter.location, ParameterLocation):
                raise ValueError(
                    f"Invalid parameter location: {parameter.location}"
                )

            if (
                parameter.location == ParameterLocation.PATH
                and not parameter.required
            ):
                raise ValueError(
                    f"Path parameter must be required: {parameter.name}"
                )

        # Validate request body
        if endpoint.request_body is not None:

            if not endpoint.request_body.content_type.strip():
                raise ValueError("Request body content type cannot be empty")

            validate_fields(
                endpoint.request_body.fields,
                "Request body",
            )

        # Validate responses
        for response in endpoint.responses:

            if not isinstance(response.status_code, int) or isinstance(
                response.status_code, bool
            ):
                raise ValueError("Response status code must be an integer")

            if not 100 <= response.status_code <= 599:
                raise ValueError(
                    f"Invalid response status code: {response.status_code}"
                )

            if not response.content_type.strip():
                raise ValueError("Response content type cannot be empty")

            validate_fields(
                response.fields,
                "Response",
            )
