from pydantic import BaseModel, Field


class FaqEntry(BaseModel):
    """FAQ 条目模型。

    这里保存的是电商售前常见问题的结构化表示。
    后续如果接入数据库，这个模型仍然可以继续复用，
    只需要把数据来源从内存列表换成数据库查询。
    """

    id: str = Field(..., description="FAQ 条目唯一标识。")
    topic: str = Field(..., description="FAQ 所属主题，例如退换货、发票、保修。")
    question: str = Field(..., description="标准问题文本。")
    answer: str = Field(..., description="标准答案文本。")
    source_label: str = Field(..., description="来源标签，用于前端展示。")
    keywords: list[str] = Field(default_factory=list, description="用于匹配用户问题的关键词。")


class FaqAskRequest(BaseModel):
    """FAQ 问答接口请求。"""

    question: str = Field(..., min_length=1, description="用户输入的售前问题。")


class FaqAskResponse(BaseModel):
    """FAQ 问答接口响应。

    这里返回的不只是答案，还包括匹配到的条目和来源。
    这样前端既能展示回答，也能告诉用户“答案来自哪里”，
    后续 Agent 也能把它作为引用证据拼进最终回复里。
    """

    question: str
    answer: str
    matched_entry: FaqEntry | None
    source_label: str
    suggestions: list[str]
