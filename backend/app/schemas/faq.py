from pydantic import BaseModel, Field


class FaqEntry(BaseModel):
    """FAQ 条目模型。"""

    id: str = Field(..., description="FAQ 条目唯一标识。")
    topic: str = Field(..., description="FAQ 所属主题。")
    question: str = Field(..., description="标准问题文本。")
    answer: str = Field(..., description="标准答案文本。")
    source_label: str = Field(..., description="来源标签。")
    keywords: list[str] = Field(default_factory=list, description="用于匹配用户问题的关键词。")


class FaqAskRequest(BaseModel):
    """FAQ 问答接口请求。"""

    question: str = Field(..., min_length=1, description="用户输入的售前问题。")


class FaqAskResponse(BaseModel):
    """FAQ 问答接口响应。

    这里不仅返回答案，还返回命中的条目和来源标签，
    方便前端展示，也方便后续 Agent 拼接引用依据。
    """

    question: str
    answer: str
    matched_entry: FaqEntry | None
    source_label: str
    suggestions: list[str]
