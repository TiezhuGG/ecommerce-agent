from app.db.repositories import get_repositories
from app.schemas.products import ProductSearchResponse, ProductSummary


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
