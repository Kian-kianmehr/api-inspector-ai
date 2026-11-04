from dataclasses import dataclass, field
from enum import Enum


# HTTP methods supported by the API Inspector
class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# Possible locations of an API parameter
class ParameterLocation(str, Enum):
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


# Represents a parameter belonging to an endpoint
@dataclass
class Parameter:
    name: str
    location: ParameterLocation
    required: bool = False
    description: str = ""


# Represents a field inside a request body
@dataclass
class BodyField:
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    fields: list[BodyField] = field(default_factory=list)


# Represents the request body of an API endpoint
@dataclass
class RequestBody:
    content_type: str = "application/json"
    required: bool = False
    description: str = ""
    fields: list[BodyField] = field(default_factory=list)


# Represents a field inside an API response
@dataclass
class ResponseField:
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    fields: list[ResponseField] = field(default_factory=list)


# Represents an API response
@dataclass
class Response:
    status_code: int
    content_type: str = "application/json"
    description: str = ""
    fields: list[ResponseField] = field(default_factory=list)


# Represents an API endpoint
@dataclass
class Endpoint:
    path: str
    method: HTTPMethod
    description: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    request_body: RequestBody | None = None
    responses: list[Response] = field(default_factory=list)


# Represents the context of an entire API
@dataclass
class APIContext:
    name: str
    base_url: str
    endpoints: list[Endpoint] = field(default_factory=list)
    description: str = ""