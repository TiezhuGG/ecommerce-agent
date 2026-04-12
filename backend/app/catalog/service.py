from __future__ import annotations

import json
import re
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
    ProductImportItem,
    ProductImportRequest,
    ProductImportResponse,
    ProductListResponse,
    ProductSearchResponse,
    ProductSummary,
    ProductUpsertRequest,
)


class ProductAdminUnavailableError(RuntimeError):
    """Raised when product admin needs a database backend but none is available."""


class ProductNotFoundError(RuntimeError):
    """Raised when a product record cannot be found."""


class ProductImportValidationError(RuntimeError):
    """Raised when bulk product import payload is invalid."""


SEARCH_SPLIT_RE = re.compile(r"[\s,/()]+")
SEARCH_COLLAPSE_RE = re.compile(r"[\s\-_/()]+")
SCENARIO_SPLIT_RE = re.compile(r"[/|,]+")


def _normalize_search_text(value: str) -> str:
    return SEARCH_COLLAPSE_RE.sub("", value.strip().lower())


def _extract_search_terms(value: str) -> set[str]:
    lowered = value.strip().lower()
    if not lowered:
        return set()

    terms = {lowered}
    collapsed = _normalize_search_text(lowered)
    if collapsed:
        terms.add(collapsed)

    for token in SEARCH_SPLIT_RE.split(lowered):
        normalized = token.strip().lower()
        if not normalized:
            continue
        terms.add(normalized)
        collapsed_token = _normalize_search_text(normalized)
        if collapsed_token:
            terms.add(collapsed_token)

    return {term for term in terms if term}


def _product_search_phrases(product: ProductSummary) -> list[str]:
    scenario_parts = [part.strip() for part in SCENARIO_SPLIT_RE.split(product.scenario) if part.strip()]
    return [
        product.name,
        product.category,
        product.brand,
        product.summary,
        *product.aliases,
        *scenario_parts,
        *product.tags,
        *product.specs,
        product.id,
    ]


def _product_search_terms(product: ProductSummary) -> set[str]:
    searchable = set()
    for phrase in _product_search_phrases(product):
        searchable.update(_extract_search_terms(phrase))
    return searchable


def _keyword_match_score(product: ProductSummary, keyword: str) -> int:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return 1

    collapsed_keyword = _normalize_search_text(normalized_keyword)
    phrases = [phrase.strip() for phrase in _product_search_phrases(product) if phrase.strip()]
    search_terms = _product_search_terms(product)
    score = 0

    for phrase in phrases:
        lowered_phrase = phrase.lower()
        if normalized_keyword in lowered_phrase:
            score = max(score, 120)
        if lowered_phrase in normalized_keyword:
            score += 24

        collapsed_phrase = _normalize_search_text(lowered_phrase)
        if collapsed_keyword and collapsed_phrase:
            if collapsed_keyword in collapsed_phrase:
                score = max(score, 105)
            if collapsed_phrase in collapsed_keyword:
                score += 20

    matched_terms = [
        term
        for term in _extract_search_terms(keyword)
        if len(term) >= 2 and any(term in candidate for candidate in search_terms)
    ]
    score += len(set(matched_terms)) * 12

    return score


def _matches_keyword(product: ProductSummary, keyword: str) -> bool:
    """Execute explainable keyword matching with alias and model-token support."""

    return _keyword_match_score(product, keyword) > 0


def infer_product_ids_from_text(text: str, *, limit: int = 3) -> list[str]:
    """Infer mentioned product IDs from free-form text."""

    normalized = text.strip()
    if not normalized:
        return []

    matched = [
        (product.id, _keyword_match_score(product, normalized))
        for product in get_repositories().products.list_products()
    ]
    sorted_matches = sorted(
        (item for item in matched if item[1] >= 24),
        key=lambda item: (-item[1], item[0]),
    )
    return [product_id for product_id, _ in sorted_matches[:limit]]


def search_products(
    *,
    keyword: str = "",
    category: str = "",
    brand: str = "",
    max_price: int | None = None,
) -> ProductSearchResponse:
    """Search products using structured filters."""

    products = get_repositories().products.list_products()
    scored_matches = [
        (product, _keyword_match_score(product, keyword))
        for product in products
        if (not category or product.category == category)
        and (not brand or product.brand == brand)
        and (max_price is None or product.price <= max_price)
    ]
    matched_items = [
        product
        for product, score in sorted(
            (item for item in scored_matches if (not keyword or item[1] > 0)),
            key=lambda item: (-item[1], item[0].category, item[0].price, item[0].name),
        )
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
        aliases=_normalize_string_list(payload.aliases),
        tags=_normalize_string_list(payload.tags),
        specs=_normalize_string_list(payload.specs),
        official_url=payload.official_url.strip(),
    )


def _build_product_from_import_item(item: ProductImportItem) -> ProductSummary:
    product_id = (item.id or "").strip() or f"product-{uuid.uuid4().hex[:12]}"
    return ProductSummary(
        id=product_id,
        name=item.name.strip(),
        category=item.category.strip(),
        brand=item.brand.strip(),
        price=item.price,
        price_note=item.price_note.strip(),
        summary=item.summary.strip(),
        scenario=item.scenario.strip(),
        aliases=_normalize_string_list(item.aliases),
        tags=_normalize_string_list(item.tags),
        specs=_normalize_string_list(item.specs),
        official_url=item.official_url.strip(),
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
                    aliases_json=json.dumps(product.aliases, ensure_ascii=False),
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
            row.aliases_json = json.dumps(product.aliases, ensure_ascii=False)
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


def export_products() -> ProductListResponse:
    return list_products_admin()


def import_products(payload: ProductImportRequest) -> ProductImportResponse:
    backend = _require_product_admin_backend()
    mode = payload.mode.strip().lower() or "upsert"
    if mode not in {"upsert", "replace"}:
        raise ProductImportValidationError("Product import mode only supports upsert or replace.")
    if not payload.items:
        raise ProductImportValidationError("Product import payload cannot be empty.")

    products = [_build_product_from_import_item(item) for item in payload.items]

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for product in products:
        if product.id in seen_ids:
            duplicate_ids.add(product.id)
            continue
        seen_ids.add(product.id)
    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise ProductImportValidationError(f"Duplicate product ids found in import payload: {duplicates}")

    created_count = 0
    updated_count = 0

    try:
        with session_scope() as session:
            if mode == "replace":
                session.query(ProductRecord).delete()
                for product in products:
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
                            aliases_json=json.dumps(product.aliases, ensure_ascii=False),
                            tags_json=json.dumps(product.tags, ensure_ascii=False),
                            specs_json=json.dumps(product.specs, ensure_ascii=False),
                            official_url=product.official_url,
                        )
                    )
                created_count = len(products)
                session.commit()
            else:
                for product in products:
                    row = session.get(ProductRecord, product.id)
                    if row is None:
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
                                aliases_json=json.dumps(product.aliases, ensure_ascii=False),
                                tags_json=json.dumps(product.tags, ensure_ascii=False),
                                specs_json=json.dumps(product.specs, ensure_ascii=False),
                                official_url=product.official_url,
                            )
                        )
                        created_count += 1
                        continue

                    row.name = product.name
                    row.category = product.category
                    row.brand = product.brand
                    row.price = product.price
                    row.price_note = product.price_note
                    row.summary = product.summary
                    row.scenario = product.scenario
                    row.aliases_json = json.dumps(product.aliases, ensure_ascii=False)
                    row.tags_json = json.dumps(product.tags, ensure_ascii=False)
                    row.specs_json = json.dumps(product.specs, ensure_ascii=False)
                    row.official_url = product.official_url
                    updated_count += 1
                session.commit()
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise ProductAdminUnavailableError(f"Unable to import products right now: {exc}") from exc

    return ProductImportResponse(
        mode=mode,
        imported_count=len(products),
        created_count=created_count,
        updated_count=updated_count,
        backend=backend,
    )
