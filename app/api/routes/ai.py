from dataclasses import asdict
from enum import Enum

from fastapi import APIRouter, HTTPException

from app.api.schemas.requests import (
    TestGenerationRequest,
    ResultAnalysisRequest,
)
from app.api.converters import convert_api_context

from app.core.ai.models import (
    AIRequest,
    AIRequestType,
)
from app.core.ai.ollama_engine import OllamaAI


router = APIRouter()

engine = OllamaAI()


def serialize_result(value):
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, list):
        return [serialize_result(item) for item in value]

    if isinstance(value, dict):
        return {
            key: serialize_result(item)
            for key, item in value.items()
        }

    if hasattr(value, "__dataclass_fields__"):
        return serialize_result(asdict(value))

    return value


@router.post("/test-generation")
def generate_tests(payload: TestGenerationRequest):
    try:
        api_context = convert_api_context(payload.api_context)

        ai_request = AIRequest(
            request_type=AIRequestType.TEST_GENERATION,
            api_context=api_context,
            instructions=payload.instructions,
        )

        result = engine.generate_tests(ai_request)

        return serialize_result(result)

    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI engine is currently unavailable.",
        )


@router.post("/result-analysis")
def analyze_results(payload: ResultAnalysisRequest):
    try:
        api_context = convert_api_context(payload.api_context)

        ai_request = AIRequest(
            request_type=AIRequestType.RESULT_ANALYSIS,
            api_context=api_context,
            test_results=payload.test_results,
            instructions=payload.instructions,
        )

        result = engine.analyze_results(ai_request)

        return serialize_result(result)

    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI engine is currently unavailable.",
        )