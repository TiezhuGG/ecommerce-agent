from pydantic import BaseModel, Field

from app.schemas.products import ProductSummary


class CompareRequest(BaseModel):
    """商品对比请求。"""

    product_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="要参与对比的商品 id 列表，当前限制为 2 到 3 个。",
    )


class CompareResponse(BaseModel):
    """商品对比响应。"""

    compared_products: list[ProductSummary]
    summary: str
    cheapest_product_name: str
    most_expensive_product_name: str
    price_gap: int
    highlights: list[str]
