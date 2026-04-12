from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    phase: str
    data_backend: str
    database_configured_backend: str
    database_runtime_status: str
    database_runtime_message: str
    database_persistence_enabled: bool


class DatabaseSmokeResponse(BaseModel):
    configured_backend: str
    runtime_backend: str
    runtime_status: str
    persistence_enabled: bool
    runtime_message: str
    product_total: int
    faq_total: int
    created_product_id: str
    created_faq_entry_id: str
    persisted_run_id: str
