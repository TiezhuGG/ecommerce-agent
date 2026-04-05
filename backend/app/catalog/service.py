from app.catalog.data import PRODUCT_CATALOG
from app.schemas.products import ProductSearchResponse, ProductSummary


def _matches_keyword(product: ProductSummary, keyword: str) -> bool:
    """执行最小可解释的关键词匹配。

    当前阶段先不接入向量检索，也不让 LLM 直接负责商品事实搜索，
    而是保留一个稳定、可预测、可复用的业务检索工具。
    后续无论是 LangChain 还是 LangGraph，本质上都应该调用这类工具。
    """

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
    """按结构化条件搜索商品目录。"""

    matched_items = [
        product
        for product in PRODUCT_CATALOG
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
        applied_filters.append(f"预算上限：¥{max_price}")

    return ProductSearchResponse(
        items=matched_items,
        total=len(matched_items),
        applied_filters=applied_filters,
        available_categories=sorted({product.category for product in PRODUCT_CATALOG}),
        available_brands=sorted({product.brand for product in PRODUCT_CATALOG}),
    )
