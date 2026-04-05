from pydantic import BaseModel, Field


class ProductSummary(BaseModel):
    """商品卡片数据模型。

    这个模型对应前端商品列表区里的一张商品卡片。
    后续无论是普通搜索、商品对比，还是 Agent 推荐，都应该优先复用这份结构，
    这样可以保证“商品事实”来自统一的数据源，而不是散落在各个模块里。
    """

    id: str = Field(..., description="商品唯一标识，后续对比、详情、埋点都会用到。")
    name: str = Field(..., description="真实存在的商品品牌与型号。")
    category: str = Field(..., description="商品分类，用于筛选和统计。")
    brand: str = Field(..., description="品牌名，用于筛选和展示。")
    price: int = Field(..., description="演示参考价，单位为人民币元。")
    price_note: str = Field(..., description="价格说明，强调这不是实时电商价格。")
    summary: str = Field(..., description="商品简短卖点，用于卡片摘要展示。")
    scenario: str = Field(..., description="适用场景，方便做导购推荐。")
    tags: list[str] = Field(default_factory=list, description="标签列表，用于展示和简单检索。")
    specs: list[str] = Field(default_factory=list, description="核心规格列表，用于商品卡片和对比。")
    official_url: str = Field(..., description="官方产品页面地址，用于增强真实感和后续溯源。")


class ProductSearchResponse(BaseModel):
    """商品搜索接口响应。

    这里不仅返回商品列表，还会把筛选摘要、分类列表、品牌列表一并返回。
    这样前端就可以把“数据结果”和“筛选控件依赖的数据”统一放在同一个响应里，
    对教学和后续演进都更直观。
    """

    items: list[ProductSummary]
    total: int
    applied_filters: list[str]
    available_categories: list[str]
    available_brands: list[str]
