from pydantic import BaseModel, Field


class FaqEntry(BaseModel):
    """知识库文档模型。

    这里虽然还沿用 faq 命名，但语义已经从“固定问答”升级成“可检索的知识文档”。
    这样做的好处是：不用推翻已有接口，就能把 FAQ 工具逐步演进成知识库工具。
    """

    id: str = Field(..., description="知识文档唯一标识")
    topic: str = Field(..., description="所属主题")
    question: str = Field(..., description="文档的标准问题标题")
    answer: str = Field(..., description="文档的标准短答案")
    source_label: str = Field(..., description="来源标签")
    keywords: list[str] = Field(default_factory=list, description="检索关键词")
    body: str = Field(default="", description="更完整的知识正文，用于切分检索片段")


class FaqCitation(BaseModel):
    """知识库命中的引用片段。"""

    entry_id: str = Field(..., description="命中的知识文档 ID")
    title: str = Field(..., description="命中文档标题")
    snippet: str = Field(..., description="命中的片段摘要")
    source_label: str = Field(..., description="片段来源标签")
    score: float = Field(..., description="本地检索得分")


class FaqAskRequest(BaseModel):
    """知识库查询请求。"""

    question: str = Field(..., min_length=1, description="用户输入的售前问题")


class FaqAskResponse(BaseModel):
    """知识库查询响应。"""

    question: str
    answer: str
    matched_entry: FaqEntry | None
    source_label: str
    suggestions: list[str]
    citations: list[FaqCitation] = Field(default_factory=list)
    retrieval_mode: str = Field(default="knowledge-rag-v1")
