from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    """商品卡片数据模型。

    这份结构会被商品搜索、商品对比和后续 Agent 推荐共同复用。
    这样项目里的“商品事实”只有一份来源，便于维护，也更贴近企业项目的分层方式。
    """

    id: str = Field(..., description="商品唯一标识。")
    name: str = Field(..., description="真实存在的品牌与型号名称。")
    category: str = Field(..., description="商品分类。")
    brand: str = Field(..., description="品牌名称。")
    price: int = Field(..., description="演示参考价，单位为人民币元。")
    price_note: str = Field(..., description="价格说明。")
    summary: str = Field(..., description="商品卖点摘要。")
    scenario: str = Field(..., description="适用场景。")
    tags: list[str] = Field(default_factory=list, description="用于展示和简单检索的标签。")
    specs: list[str] = Field(default_factory=list, description="核心规格列表。")
    official_url: str = Field(..., description="官方产品页地址。")


class ProductSearchResponse(BaseModel):
    """商品搜索接口响应。

    除了返回商品列表，还顺手把筛选摘要、分类列表和品牌列表带回前端，
    方便页面一次请求就完成主要渲染。
    """

    items: list[ProductSummary]
    total: int
    applied_filters: list[str]
    available_categories: list[str]
    available_brands: list[str]
