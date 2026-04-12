from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass

from app.catalog.service import create_product, delete_product, list_products_admin
from app.db.models import AgentRunRecord
from app.db.repositories import get_database_runtime_info
from app.db.service import (
    DatabaseUnavailableError,
    SQLAlchemyError,
    get_agent_run,
    initialize_database,
    persist_agent_run,
    session_scope,
)
from app.faq.service import create_faq_entry, delete_faq_entry, list_faq_entries_admin
from app.schemas.faq import FaqEntryUpsertRequest
from app.schemas.products import ProductUpsertRequest


@dataclass(slots=True)
class DatabaseSmokeReport:
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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cleanup_agent_run(run_id: str) -> None:
    if AgentRunRecord is None:
        return

    with session_scope() as session:
        row = session.get(AgentRunRecord, run_id)
        if row is not None:
            session.delete(row)
            session.commit()


def run_database_smoke_checks(expect_backend: str | None = None) -> DatabaseSmokeReport:
    runtime = get_database_runtime_info()

    if expect_backend and runtime.configured_backend != expect_backend:
        raise RuntimeError(
            f"当前 DATABASE_URL 配置目标为 {runtime.configured_backend}，不符合预期 {expect_backend}。"
        )

    if not runtime.persistence_enabled:
        raise RuntimeError(
            "当前数据库持久化未启用，无法执行数据库 smoke 校验。"
            f"当前状态: {runtime.status} / {runtime.message}"
        )

    ok, message = initialize_database()
    if not ok:
        raise RuntimeError(f"数据库初始化失败: {message}")

    try:
        products = list_products_admin()
        faq_entries = list_faq_entries_admin()
    except (DatabaseUnavailableError, SQLAlchemyError, RuntimeError) as exc:
        raise RuntimeError(f"无法读取数据库中的商品或知识库条目: {exc}") from exc

    created_product_id = ""
    created_faq_entry_id = ""
    persisted_run_id = ""

    try:
        created_product = create_product(
            ProductUpsertRequest(
                name="Smoke Test Product",
                category="Smoke Test",
                brand="Codex",
                price=1234,
                price_note="Smoke test only",
                summary="Temporary record created by database smoke verification.",
                scenario="Database runtime verification",
                tags=["smoke", "database"],
                specs=["temporary", "cleanup-after-check"],
                official_url="https://example.com/smoke-test-product",
            )
        )
        created_product_id = created_product.id

        created_entry = create_faq_entry(
            FaqEntryUpsertRequest(
                topic="Smoke Test",
                question="这是一条数据库 smoke test FAQ 吗？",
                answer="是，这条 FAQ 仅用于数据库联调自检。",
                source_label="Smoke Test",
                keywords=["smoke", "database", "verification"],
                body="Temporary FAQ entry created by database smoke verification.",
            )
        )
        created_faq_entry_id = created_entry.id

        persisted_run_id = persist_agent_run(
            {
                "run_id": f"smoke-run-{uuid.uuid4().hex[:12]}",
                "thread_id": f"smoke-thread-{uuid.uuid4().hex[:12]}",
                "message": "database smoke test",
                "route": "faq",
                "route_reasoning": "database smoke verification",
                "final_answer": "Smoke verification completed.",
                "warnings": [],
                "tool_calls": [],
                "selected_product_ids": [],
                "conversation_context": [],
                "recommended_product_ids": [],
                "parsed_intent": None,
                "faq_result": None,
                "compare_result": None,
                "providers": {
                    "route_provider": "smoke-check",
                    "intent_provider": "",
                    "answer_provider": "smoke-check",
                    "retrieval_provider": "",
                },
                "provider": "smoke-check",
                "model": "smoke-check",
                "graph_runtime": "smoke-check",
            }
        )

        persisted_run = get_agent_run(persisted_run_id)
        if persisted_run is None:
            raise RuntimeError("数据库 smoke 校验写入的 Agent 运行记录无法再次读取。")
    finally:
        if created_product_id:
            delete_product(created_product_id)
        if created_faq_entry_id:
            delete_faq_entry(created_faq_entry_id)
        if persisted_run_id:
            _cleanup_agent_run(persisted_run_id)

    return DatabaseSmokeReport(
        configured_backend=runtime.configured_backend,
        runtime_backend=runtime.runtime_backend,
        runtime_status=runtime.status,
        persistence_enabled=runtime.persistence_enabled,
        runtime_message=runtime.message,
        product_total=len(products.items),
        faq_total=len(faq_entries.items),
        created_product_id=created_product_id,
        created_faq_entry_id=created_faq_entry_id,
        persisted_run_id=persisted_run_id,
    )
