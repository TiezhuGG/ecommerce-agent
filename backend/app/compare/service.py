from app.catalog.data import PRODUCT_CATALOG
from app.schemas.compare import CompareResponse
from app.schemas.products import ProductSummary


def compare_products(product_ids: list[str]) -> CompareResponse:
    """按商品 id 做对比分析。"""

    product_map = {product.id: product for product in PRODUCT_CATALOG}
    compared_products = [product_map[product_id] for product_id in product_ids if product_id in product_map]

    if len(compared_products) < 2:
        raise ValueError("至少需要 2 个有效商品才能进行对比。")

    sorted_by_price = sorted(compared_products, key=lambda product: product.price)
    cheapest = sorted_by_price[0]
    expensive = sorted_by_price[-1]
    price_gap = expensive.price - cheapest.price

    highlights = [
        f"价格最低的是 {cheapest.name}，参考价为 ¥{cheapest.price}",
        f"价格最高的是 {expensive.name}，参考价为 ¥{expensive.price}",
        f"当前对比商品的价格跨度为 ¥{price_gap}",
    ]

    scenarios = "、".join(dict.fromkeys(product.scenario for product in compared_products))
    summary = (
        f"本次对比共涉及 {len(compared_products)} 款商品。"
        f"如果你更关注预算控制，可以优先看 {cheapest.name}；"
        f"如果你更关注高定位配置，可以重点关注 {expensive.name}。"
        f"这些商品主要覆盖的使用场景包括：{scenarios}。"
    )

    return CompareResponse(
        compared_products=compared_products,
        summary=summary,
        cheapest_product_name=cheapest.name,
        most_expensive_product_name=expensive.name,
        price_gap=price_gap,
        highlights=highlights,
    )
