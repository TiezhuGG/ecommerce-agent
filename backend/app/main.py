from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.router import router as agent_router
from app.catalog.router import router as catalog_router
from app.compare.router import router as compare_router
from app.config import settings
from app.faq.router import router as faq_router
from app.intent.router import router as intent_router


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="教学优先的电商导购 Agent 后端。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router)
app.include_router(compare_router)
app.include_router(faq_router)
app.include_router(intent_router)
app.include_router(agent_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "phase": "phase-8-langgraph-agent",
    }
