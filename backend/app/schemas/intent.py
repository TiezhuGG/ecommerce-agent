from pydantic import BaseModel, Field


class IntentParseRequest(BaseModel):
    """意图解析接口请求。"""

    query: str = Field(..., min_length=1, description="用户输入的自然语言导购需求。")


class IntentSearchFilters(BaseModel):
    """解析后可直接用于商品搜索的结构化筛选条件。"""

    keyword: str = Field(default="", description="用于商品搜索的关键词。")
    category: str = Field(default="", description="解析出的商品分类。")
    brand: str = Field(default="", description="解析出的品牌。")
    max_price: int | None = Field(default=None, description="解析出的预算上限。")


class IntentParseResponse(BaseModel):
    """意图解析接口响应。

    模型只负责把自然语言整理成结构化条件，
    真正的商品事实仍然必须来自 `/products` 业务接口。
    """

    query: str
    search_filters: IntentSearchFilters
    scenario: str
    priorities: list[str]
    applied_filters: list[str]
    reasoning_summary: str
    provider: str
    model: str
