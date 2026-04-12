from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol
from urllib.parse import urlparse

from app.config import settings
from app.db.models import FaqEntryRecord, ProductRecord, SQLALCHEMY_AVAILABLE
from app.db.service import (
    DatabaseUnavailableError,
    SQLAlchemyError,
    faq_from_record,
    initialize_database,
    product_from_record,
    session_scope,
)
from app.schemas.faq import FaqEntry
from app.schemas.products import ProductSummary
from app.seed.bootstrap import load_seed_faq_entries, load_seed_products

if SQLALCHEMY_AVAILABLE:
    from sqlalchemy import select
else:  # pragma: no cover - depends on local environment
    select = None


class ProductRepository(Protocol):
    def list_products(self) -> list[ProductSummary]: ...


class FaqRepository(Protocol):
    def list_entries(self) -> list[FaqEntry]: ...


@dataclass(slots=True)
class InMemoryProductRepository:
    products: list[ProductSummary]

    def list_products(self) -> list[ProductSummary]:
        return [product.model_copy(deep=True) for product in self.products]


@dataclass(slots=True)
class InMemoryFaqRepository:
    entries: list[FaqEntry]

    def list_entries(self) -> list[FaqEntry]:
        return [entry.model_copy(deep=True) for entry in self.entries]


class SqlAlchemyProductRepository:
    def list_products(self) -> list[ProductSummary]:
        if ProductRecord is None or select is None:
            raise DatabaseUnavailableError("SQLAlchemy product repository is unavailable.")
        with session_scope() as session:
            rows = session.scalars(select(ProductRecord).order_by(ProductRecord.category, ProductRecord.price)).all()
        return [product_from_record(row) for row in rows]


class SqlAlchemyFaqRepository:
    def list_entries(self) -> list[FaqEntry]:
        if FaqEntryRecord is None or select is None:
            raise DatabaseUnavailableError("SQLAlchemy FAQ repository is unavailable.")
        with session_scope() as session:
            rows = session.scalars(select(FaqEntryRecord).order_by(FaqEntryRecord.topic, FaqEntryRecord.id)).all()
        return [faq_from_record(row) for row in rows]


@dataclass(slots=True)
class RepositoryBundle:
    products: ProductRepository
    faq: FaqRepository
    backend: str


@dataclass(slots=True)
class DatabaseRuntimeInfo:
    configured_backend: str
    runtime_backend: str
    status: str
    message: str
    persistence_enabled: bool


def _build_in_memory_bundle() -> RepositoryBundle:
    return RepositoryBundle(
        products=InMemoryProductRepository(load_seed_products()),
        faq=InMemoryFaqRepository(load_seed_faq_entries()),
        backend="in-memory-seed",
    )


def _database_backend_name() -> str:
    scheme = urlparse(settings.database_url.strip()).scheme.lower()
    if scheme.startswith("postgres"):
        return "sqlalchemy-postgresql"
    if scheme.startswith("sqlite"):
        return "sqlalchemy-sqlite"
    return "sqlalchemy-database"


def _configured_database_backend_name() -> str:
    database_url = settings.database_url.strip()
    if not database_url:
        return "not-configured"

    scheme = urlparse(database_url).scheme.lower()
    if scheme.startswith("postgres"):
        return "postgresql"
    if scheme.startswith("sqlite"):
        return "sqlite"
    return scheme or "unknown"


@lru_cache(maxsize=1)
def get_repositories() -> RepositoryBundle:
    database_url = settings.database_url.strip()
    if not database_url:
        return _build_in_memory_bundle()

    if not SQLALCHEMY_AVAILABLE:
        return RepositoryBundle(
            products=InMemoryProductRepository(load_seed_products()),
            faq=InMemoryFaqRepository(load_seed_faq_entries()),
            backend="database-configured-missing-deps-fallback-seed",
        )

    try:
        ok, _ = initialize_database()
        if ok:
            return RepositoryBundle(
                products=SqlAlchemyProductRepository(),
                faq=SqlAlchemyFaqRepository(),
                backend=_database_backend_name(),
            )
    except (DatabaseUnavailableError, SQLAlchemyError):
        pass

    return RepositoryBundle(
        products=InMemoryProductRepository(load_seed_products()),
        faq=InMemoryFaqRepository(load_seed_faq_entries()),
        backend="database-configured-fallback-seed",
    )


def get_database_runtime_info() -> DatabaseRuntimeInfo:
    repositories = get_repositories()
    configured_backend = _configured_database_backend_name()

    if configured_backend == "not-configured":
        return DatabaseRuntimeInfo(
            configured_backend=configured_backend,
            runtime_backend=repositories.backend,
            status="seed-only",
            message="未配置 DATABASE_URL，当前使用内存 seed 数据，重启后不会保留后台改动和 Agent 日志。",
            persistence_enabled=False,
        )

    if repositories.backend.startswith("sqlalchemy-"):
        if configured_backend == "sqlite":
            message = "当前数据库已连通，正在使用 SQLite 持久化数据，适合本地开发和单机验证。"
        elif configured_backend == "postgresql":
            message = "当前数据库已连通，正在使用 PostgreSQL 持久化数据，适合上线环境。"
        else:
            message = "当前数据库已连通，后台数据和 Agent 日志会写入已配置数据库。"

        return DatabaseRuntimeInfo(
            configured_backend=configured_backend,
            runtime_backend=repositories.backend,
            status="ready",
            message=message,
            persistence_enabled=True,
        )

    if not SQLALCHEMY_AVAILABLE:
        message = "已配置 DATABASE_URL，但当前环境缺少 SQLAlchemy 依赖，已回退到内存 seed 数据。"
    else:
        message = "已配置 DATABASE_URL，但当前数据库不可用，已回退到内存 seed 数据。"

    return DatabaseRuntimeInfo(
        configured_backend=configured_backend,
        runtime_backend=repositories.backend,
        status="fallback-seed",
        message=message,
        persistence_enabled=False,
    )
