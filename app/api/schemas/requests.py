from pydantic import BaseModel, Field
from typing import Optional

from app.core.context.models import (
    HTTPMethod,
    ParameterLocation,
)


class BodyFieldSchema(BaseModel):
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    fields: list["BodyFieldSchema"] = Field(default_factory=list)


class RequestBodySchema(BaseModel):
    content_type: str = "application/json"
    required: bool = False
    description: str = ""
    fields: list[BodyFieldSchema] = Field(default_factory=list)


class ResponseFieldSchema(BaseModel):
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    fields: list["ResponseFieldSchema"] = Field(default_factory=list)


class ResponseSchema(BaseModel):
    status_code: int
    content_type: str = "application/json"
    description: str = ""
    fields: list[ResponseFieldSchema] = Field(default_factory=list)


class ParameterSchema(BaseModel):
    name: str
    location: ParameterLocation
    required: bool = False
    description: str = ""


class EndpointSchema(BaseModel):
    path: str
    method: HTTPMethod
    description: str = ""
    parameters: list[ParameterSchema] = Field(default_factory=list)
    request_body: Optional[RequestBodySchema] = None
    responses: list[ResponseSchema] = Field(default_factory=list)


class APIContextSchema(BaseModel):
    name: str
    base_url: str
    endpoints: list[EndpointSchema] = Field(default_factory=list)
    description: str = ""


class TestGenerationRequest(BaseModel):
    api_context: APIContextSchema
    instructions: str = ""


class ResultAnalysisRequest(BaseModel):
    api_context: APIContextSchema
    test_results: list[dict] = Field(default_factory=list)
    instructions: str = ""