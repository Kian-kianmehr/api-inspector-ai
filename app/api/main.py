from fastapi import FastAPI
from app.api.routes.ai import router as ai_router

app = FastAPI(
    title="API Inspector AI",
    description="AI-powered API testing and analysis service",
    version="1.0.0"
)
app.include_router(ai_router,prefix="/v1")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "api-inspector-ai"
    }