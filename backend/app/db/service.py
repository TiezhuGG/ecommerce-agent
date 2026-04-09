from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import lru_cache
from typing import Iterator

from app.config import settings
from app.db.models import AgentRunRecord, Base, FaqEntryRecord, ProductRecord, SQLALCHEMY_AVAILABLE
from app.schemas.faq import FaqEntry
from app.schemas.products import ProductSummary
from app.seed.bootstrap import load_seed_faq_entries, load_seed_products

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import create_engine, inspect, select, text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session, sessionmaker
else:  # pragma: no cover - depends on local environment
    Session = object  # type: ignore[assignment]
    sessionmaker = None
    create_engine = None
    inspect = None
    select = None
    text = None

    class SQLAlchemyError(RuntimeError):
        pass


class DatabaseUnavailableError(RuntimeError):
    """Raised when the configured database cannot be used."""


@lru_cache(maxsize=1)
def get_engine():
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")

    database_url = settings.database_url.strip()
    if not database_url:
        raise DatabaseUnavailableError("DATABASE_URL is not configured.")

    assert create_engine is not None
    return create_engine(database_url, future=True, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory():
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")

    assert sessionmaker is not None
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def reset_db_runtime_state() -> None:
    try:
        engine = get_engine()
    except DatabaseUnavailableError:
        engine = None

    if engine is not None:
        engine.dispose()

    get_engine.cache_clear()
    get_session_factory.cache_clear()


@contextmanager
def session_scope() -> Iterator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _product_to_record(product: ProductSummary):
    if ProductRecord is None:
        raise DatabaseUnavailableError("SQLAlchemy models are unavailable.")

    return ProductRecord(
        id=product.id,
        name=product.name,
        category=product.category,
        brand=product.brand,
        price=product.price,
        price_note=product.price_note,
        summary=product.summary,
        scenario=product.scenario,
        tags_json=json.dumps(product.tags, ensure_ascii=False),
        specs_json=json.dumps(product.specs, ensure_ascii=False),
        official_url=product.official_url,
    )


def _faq_to_record(entry: FaqEntry):
    if FaqEntryRecord is None:
        raise DatabaseUnavailableError("SQLAlchemy models are unavailable.")

    return FaqEntryRecord(
        id=entry.id,
        topic=entry.topic,
        question=entry.question,
        answer=entry.answer,
        source_label=entry.source_label,
        keywords_json=json.dumps(entry.keywords, ensure_ascii=False),
        body=entry.body,
    )


def product_from_record(record) -> ProductSummary:
    return ProductSummary(
        id=record.id,
        name=record.name,
        category=record.category,
        brand=record.brand,
        price=record.price,
        price_note=record.price_note,
        summary=record.summary,
        scenario=record.scenario,
        tags=json.loads(record.tags_json),
        specs=json.loads(record.specs_json),
        official_url=record.official_url,
    )


def faq_from_record(record) -> FaqEntry:
    return FaqEntry(
        id=record.id,
        topic=record.topic,
        question=record.question,
        answer=record.answer,
        source_label=record.source_label,
        keywords=json.loads(record.keywords_json),
        body=record.body,
    )


def initialize_database() -> tuple[bool, str]:
    if not SQLALCHEMY_AVAILABLE:
        return False, "SQLAlchemy is not installed."

    try:
        engine = get_engine()
        assert Base.metadata is not None
        Base.metadata.create_all(engine)
        ensure_agent_run_schema()
        seed_database_if_empty()
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        return False, str(exc)

    return True, "database-ready"


def seed_database_if_empty() -> None:
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")

    if ProductRecord is None or FaqEntryRecord is None:
        raise DatabaseUnavailableError("SQLAlchemy models are unavailable.")

    assert select is not None
    with session_scope() as session:
        existing_product_ids = set(session.scalars(select(ProductRecord.id)).all())
        existing_faq_ids = set(session.scalars(select(FaqEntryRecord.id)).all())

        missing_products = [
            product for product in load_seed_products() if product.id not in existing_product_ids
        ]
        missing_faq_entries = [
            entry for entry in load_seed_faq_entries() if entry.id not in existing_faq_ids
        ]

        if missing_products:
            session.add_all(_product_to_record(product) for product in missing_products)
        if missing_faq_entries:
            session.add_all(_faq_to_record(entry) for entry in missing_faq_entries)

        if missing_products or missing_faq_entries:
            session.commit()


def persist_agent_run(payload: dict[str, object]) -> str:
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")
    if AgentRunRecord is None:
        raise DatabaseUnavailableError("Agent run model is unavailable.")

    run_id = str(payload.get("run_id") or uuid.uuid4())
    created_at = str(payload.get("created_at") or datetime.now(UTC).isoformat())

    with session_scope() as session:
        session.add(
            AgentRunRecord(
                id=run_id,
                thread_id=str(payload.get("thread_id") or run_id),
                created_at=created_at,
                message=str(payload.get("message", "")),
                route=str(payload.get("route", "")),
                route_reasoning=str(payload.get("route_reasoning", "")),
                final_answer=str(payload.get("final_answer", "")),
                warnings_json=json.dumps(payload.get("warnings", []), ensure_ascii=False),
                tool_calls_json=json.dumps(payload.get("tool_calls", []), ensure_ascii=False),
                selected_product_ids_json=json.dumps(payload.get("selected_product_ids", []), ensure_ascii=False),
                conversation_context_json=json.dumps(payload.get("conversation_context", []), ensure_ascii=False),
                recommended_product_ids_json=json.dumps(payload.get("recommended_product_ids", []), ensure_ascii=False),
                parsed_intent_json=json.dumps(payload.get("parsed_intent"), ensure_ascii=False),
                faq_result_json=json.dumps(payload.get("faq_result"), ensure_ascii=False),
                compare_result_json=json.dumps(payload.get("compare_result"), ensure_ascii=False),
                providers_json=json.dumps(payload.get("providers", {}), ensure_ascii=False),
                provider=str(payload.get("provider", "")),
                model=str(payload.get("model", "")),
                graph_runtime=str(payload.get("graph_runtime", "")),
            )
        )
        session.commit()

    return run_id


def _deserialize_json_field(raw_value: str | None) -> object:
    if raw_value is None or raw_value == "":
        return None
    return json.loads(raw_value)


def _agent_run_row_to_payload(row: AgentRunRecord) -> dict[str, object]:
    providers = _deserialize_json_field(row.providers_json)
    if not isinstance(providers, dict):
        providers = {
            "route_provider": "",
            "intent_provider": "",
            "answer_provider": row.provider,
            "retrieval_provider": "",
        }

    return {
        "run_id": row.id,
        "thread_id": row.thread_id,
        "created_at": row.created_at,
        "message": row.message,
        "route": row.route,
        "route_reasoning": row.route_reasoning,
        "final_answer": row.final_answer,
        "warnings": _deserialize_json_field(row.warnings_json) or [],
        "tool_calls": _deserialize_json_field(row.tool_calls_json) or [],
        "selected_product_ids": _deserialize_json_field(row.selected_product_ids_json) or [],
        "conversation_context": _deserialize_json_field(row.conversation_context_json) or [],
        "recommended_product_ids": _deserialize_json_field(row.recommended_product_ids_json) or [],
        "parsed_intent": _deserialize_json_field(row.parsed_intent_json),
        "faq_result": _deserialize_json_field(row.faq_result_json),
        "compare_result": _deserialize_json_field(row.compare_result_json),
        "providers": providers,
        "provider": row.provider,
        "model": row.model,
        "graph_runtime": row.graph_runtime,
    }


def ensure_agent_run_schema() -> None:
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")
    if AgentRunRecord is None:
        raise DatabaseUnavailableError("Agent run model is unavailable.")
    if inspect is None or text is None:
        raise DatabaseUnavailableError("SQLAlchemy inspection utilities are unavailable.")

    engine = get_engine()
    columns = {column["name"] for column in inspect(engine).get_columns("agent_runs")}

    with session_scope() as session:
        if "thread_id" not in columns:
            session.execute(text("ALTER TABLE agent_runs ADD COLUMN thread_id TEXT"))
            session.execute(
                text(
                    "UPDATE agent_runs "
                    "SET thread_id = id "
                    "WHERE thread_id IS NULL OR thread_id = ''"
                )
            )

        if "created_at" not in columns:
            session.execute(text("ALTER TABLE agent_runs ADD COLUMN created_at TEXT"))
            session.execute(
                text(
                    "UPDATE agent_runs "
                    "SET created_at = :created_at "
                    "WHERE created_at IS NULL OR created_at = ''"
                ),
                {"created_at": datetime.now(UTC).isoformat()},
            )

        if "providers_json" not in columns:
            session.execute(text("ALTER TABLE agent_runs ADD COLUMN providers_json TEXT"))
            session.execute(
                text(
                    "UPDATE agent_runs "
                    "SET providers_json = :providers_json "
                    "WHERE providers_json IS NULL OR providers_json = ''"
                ),
                {
                    "providers_json": json.dumps(
                        {
                            "route_provider": "",
                            "intent_provider": "",
                            "answer_provider": "",
                            "retrieval_provider": "",
                        },
                        ensure_ascii=False,
                    )
                },
            )

        if "conversation_context_json" not in columns:
            session.execute(text("ALTER TABLE agent_runs ADD COLUMN conversation_context_json TEXT"))
            session.execute(
                text(
                    "UPDATE agent_runs "
                    "SET conversation_context_json = :conversation_context_json "
                    "WHERE conversation_context_json IS NULL OR conversation_context_json = ''"
                ),
                {
                    "conversation_context_json": json.dumps([], ensure_ascii=False),
                },
            )
        session.commit()


def list_agent_runs(limit: int = 10) -> list[dict[str, object]]:
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")
    if AgentRunRecord is None:
        raise DatabaseUnavailableError("Agent run model is unavailable.")
    if select is None:
        raise DatabaseUnavailableError("SQLAlchemy select is unavailable.")

    ensure_agent_run_schema()

    normalized_limit = max(1, min(limit, 20))
    with session_scope() as session:
        rows = session.scalars(
            select(AgentRunRecord)
            .order_by(AgentRunRecord.created_at.desc(), AgentRunRecord.id.desc())
            .limit(normalized_limit)
        ).all()

    return [_agent_run_row_to_payload(row) for row in rows]


def get_agent_run(run_id: str) -> dict[str, object] | None:
    if not SQLALCHEMY_AVAILABLE:
        raise DatabaseUnavailableError("SQLAlchemy is not installed.")
    if AgentRunRecord is None:
        raise DatabaseUnavailableError("Agent run model is unavailable.")

    with session_scope() as session:
        row = session.get(AgentRunRecord, run_id)

    if row is None:
        return None

    return _agent_run_row_to_payload(row)
