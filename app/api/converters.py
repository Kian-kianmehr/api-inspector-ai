
from app.core.context.models import (
    APIContext,
    Endpoint,
    Parameter,
    RequestBody,
    BodyField,
    Response,
    ResponseField,
)

from app.api.schemas.requests import (
    APIContextSchema,
    EndpointSchema,
    ParameterSchema,
    RequestBodySchema,
    BodyFieldSchema,
    ResponseSchema,
    ResponseFieldSchema,
)


def convert_body_field(field: BodyFieldSchema) -> BodyField:
    return BodyField(
        name=field.name,
        data_type=field.data_type,
        required=field.required,
        description=field.description,
        fields=[
            convert_body_field(child)
            for child in field.fields
        ],
    )


def convert_response_field(field: ResponseFieldSchema) -> ResponseField:
    return ResponseField(
        name=field.name,
        data_type=field.data_type,
        required=field.required,
        description=field.description,
        fields=[
            convert_response_field(child)
            for child in field.fields
        ],
    )


def convert_request_body(body: RequestBodySchema | None) -> RequestBody | None:
    if body is None:
        return None

    return RequestBody(
        content_type=body.content_type,
        required=body.required,
        description=body.description,
        fields=[
            convert_body_field(field)
            for field in body.fields
        ],
    )


def convert_parameter(parameter: ParameterSchema) -> Parameter:
    return Parameter(
        name=parameter.name,
        location=parameter.location,
        required=parameter.required,
        description=parameter.description,
    )


def convert_response(response: ResponseSchema) -> Response:
    return Response(
        status_code=response.status_code,
        content_type=response.content_type,
        description=response.description,
        fields=[
            convert_response_field(field)
            for field in response.fields
        ],
    )


def convert_endpoint(endpoint: EndpointSchema) -> Endpoint:
    return Endpoint(
        path=endpoint.path,
        method=endpoint.method,
        description=endpoint.description,
        parameters=[
            convert_parameter(parameter)
            for parameter in endpoint.parameters
        ],
        request_body=convert_request_body(endpoint.request_body),
        responses=[
            convert_response(response)
            for response in endpoint.responses
        ],
    )


def convert_api_context(context: APIContextSchema) -> APIContext:
    return APIContext(
        name=context.name,
        base_url=context.base_url,
        description=context.description,
        endpoints=[
            convert_endpoint(endpoint)
            for endpoint in context.endpoints
        ],
    )
