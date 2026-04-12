from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.router import router as admin_router
from app.agent.router import router as agent_router
from app.catalog.router import router as catalog_router
from app.compare.router import router as compare_router
from app.config import settings
from app.db.repositories import get_database_runtime_info
from app.db.service import initialize_database
from app.faq.router import router as faq_router
from app.intent.router import router as intent_router
from app.schemas.system import HealthResponse


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    if settings.database_url.strip():
        initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="教学优先的电商导购 Agent 后端。",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(catalog_router)
app.include_router(compare_router)
app.include_router(faq_router)
app.include_router(intent_router)
app.include_router(agent_router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    runtime = get_database_runtime_info()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        phase="phase-9-knowledge-rag",
        data_backend=runtime.runtime_backend,
        database_configured_backend=runtime.configured_backend,
        database_runtime_status=runtime.status,
        database_runtime_message=runtime.message,
        database_persistence_enabled=runtime.persistence_enabled,
    )
