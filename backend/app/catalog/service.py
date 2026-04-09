from __future__ import annotations

import json
import uuid

from app.db.models import ProductRecord
from app.db.repositories import get_repositories
from app.db.service import (
    DatabaseUnavailableError,
    SQLAlchemyError,
    product_from_record,
    session_scope,
)
from app.schemas.products import (
    ProductDeleteResponse,
    ProductListResponse,
    ProductSearchResponse,
    ProductSummary,
    ProductUpsertRequest,
)


class ProductAdminUnavailableError(RuntimeError):
    """Raised when product admin needs a database backend but none is available."""


class ProductNotFoundError(RuntimeError):
    """Raised when a product record cannot be found."""


def _matches_keyword(product: ProductSummary, keyword: str) -> bool:
    """Execute simple explainable keyword matching."""

    normalized = keyword.strip().lower()
    if not normalized:
        return True

    haystacks = [
        product.name,
        product.category,
        product.brand,
        product.summary,
        product.scenario,
        *product.tags,
        *product.specs,
    ]
    return any(normalized in field.lower() for field in haystacks)


def search_products(
    *,
    keyword: str = "",
    category: str = "",
    brand: str = "",
    max_price: int | None = None,
) -> ProductSearchResponse:
    """Search products using structured filters."""

    products = get_repositories().products.list_products()
    matched_items = [
        product
        for product in products
        if _matches_keyword(product, keyword)
        and (not category or product.category == category)
        and (not brand or product.brand == brand)
        and (max_price is None or product.price <= max_price)
    ]

    applied_filters: list[str] = []
    if keyword:
        applied_filters.append(f"关键词：{keyword}")
    if category:
        applied_filters.append(f"分类：{category}")
    if brand:
        applied_filters.append(f"品牌：{brand}")
    if max_price is not None:
        applied_filters.append(f"预算上限：￥{max_price}")

    return ProductSearchResponse(
        items=matched_items,
        total=len(matched_items),
        applied_filters=applied_filters,
        available_categories=sorted({product.category for product in products}),
        available_brands=sorted({product.brand for product in products}),
    )


def _require_product_admin_backend() -> str:
    backend = get_repositories().backend
    if not backend.startswith("sqlalchemy-"):
        raise ProductAdminUnavailableError("当前未启用数据库商品目录存储，无法管理商品数据。")
    if ProductRecord is None:
        raise ProductAdminUnavailableError("当前数据库商品模型不可用。")
    return backend


def _normalize_string_list(items: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = item.strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(value)
    return normalized


def _build_product_model(product_id: str, payload: ProductUpsertRequest) -> ProductSummary:
    return ProductSummary(
        id=product_id,
        name=payload.name.strip(),
        category=payload.category.strip(),
        brand=payload.brand.strip(),
        price=payload.price,
        price_note=payload.price_note.strip(),
        summary=payload.summary.strip(),
        scenario=payload.scenario.strip(),
        tags=_normalize_string_list(payload.tags),
        specs=_normalize_string_list(payload.specs),
        official_url=payload.official_url.strip(),
    )


def list_products_admin() -> ProductListResponse:
    backend = _require_product_admin_backend()

    try:
        with session_scope() as session:
            rows = (
                session.query(ProductRecord)
                .order_by(ProductRecord.category.asc(), ProductRecord.brand.asc(), ProductRecord.name.asc())
                .all()
            )
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise ProductAdminUnavailableError(f"当前无法读取商品目录：{exc}") from exc

    return ProductListResponse(
        backend=backend,
        items=[product_from_record(row) for row in rows],
    )


def create_product(payload: ProductUpsertRequest) -> ProductSummary:
    _require_product_admin_backend()
    product_id = f"product-{uuid.uuid4().hex[:12]}"
    product = _build_product_model(product_id, payload)

    try:
        with session_scope() as session:
            session.add(
                ProductRecord(
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
            )
            session.commit()
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise ProductAdminUnavailableError(f"当前无法新增商品：{exc}") from exc

    return product


def update_product(product_id: str, payload: ProductUpsertRequest) -> ProductSummary:
    _require_product_admin_backend()
    product = _build_product_model(product_id, payload)

    try:
        with session_scope() as session:
            row = session.get(ProductRecord, product_id)
            if row is None:
                raise ProductNotFoundError(f"未找到 product_id={product_id} 对应的商品。")

            row.name = product.name
            row.category = product.category
            row.brand = product.brand
            row.price = product.price
            row.price_note = product.price_note
            row.summary = product.summary
            row.scenario = product.scenario
            row.tags_json = json.dumps(product.tags, ensure_ascii=False)
            row.specs_json = json.dumps(product.specs, ensure_ascii=False)
            row.official_url = product.official_url
            session.commit()
    except ProductNotFoundError:
        raise
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise ProductAdminUnavailableError(f"当前无法更新商品：{exc}") from exc

    return product


def delete_product(product_id: str) -> ProductDeleteResponse:
    _require_product_admin_backend()

    try:
        with session_scope() as session:
            row = session.get(ProductRecord, product_id)
            if row is None:
                raise ProductNotFoundError(f"未找到 product_id={product_id} 对应的商品。")
            session.delete(row)
            session.commit()
    except ProductNotFoundError:
        raise
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise ProductAdminUnavailableError(f"当前无法删除商品：{exc}") from exc

    return ProductDeleteResponse(product_id=product_id)
