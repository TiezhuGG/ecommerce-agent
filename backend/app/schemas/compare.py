from pydantic import BaseModel, Field

from app.schemas.products import ProductSummary


class CompareRequest(BaseModel):
    """商品对比接口请求。"""

    product_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="要参与对比的商品 id 列表，当前限制为 2 到 3 个。",
    )


class CompareResponse(BaseModel):
    """商品对比接口响应。

    这里既返回参与对比的商品事实，也返回后端生成的对比摘要。
    当前摘要仍然是普通业务逻辑拼接出来的，不是 AI 总结。
    这样做可以先把“对比能力”做成稳定工具，后续 Agent 再复用。
    """

    compared_products: list[ProductSummary]
    summary: str
    cheapest_product_name: str
    most_expensive_product_name: str
    price_gap: int
    highlights: list[str]
