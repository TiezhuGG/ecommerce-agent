from typing import Any

from pydantic import BaseModel, Field

from app.schemas.compare import CompareResponse
from app.schemas.faq import FaqAskResponse
from app.schemas.intent import IntentParseResponse


class AgentToolStatus(BaseModel):
    """预检阶段的工具状态。"""

    name: str
    enabled: bool
    description: str


class AgentPrecheckResponse(BaseModel):
    """Agent 启动前的预检结果。"""

    status: str
    summary: str
    model: str
    base_url: str | None
    api_style: str
    openai_sdk_available: bool
    langgraph_available: bool
    data_backend: str
    agent_log_backend: str
    catalog_total: int
    warnings: list[str]
    tools: list[AgentToolStatus]


class AgentToolCall(BaseModel):
    """Agent 在本轮对话中的工具调用记录。"""

    tool_name: str
    status: str
    summary: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class AgentChatRequest(BaseModel):
    """Agent 对话请求。"""

    message: str = Field(..., min_length=1, description="用户输入的自然语言问题或导购需求")
    selected_product_ids: list[str] = Field(
        default_factory=list,
        description="前端当前已选中的商品，用于帮助 Agent 进入商品对比场景",
    )


class AgentChatResponse(BaseModel):
    """Agent 对话结果。"""

    message: str
    selected_product_ids: list[str] = Field(default_factory=list)
    route: str
    route_reasoning: str
    final_answer: str
    warnings: list[str]
    tool_calls: list[AgentToolCall]
    parsed_intent: IntentParseResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)
    faq_result: FaqAskResponse | None = None
    compare_result: CompareResponse | None = None
    provider: str
    model: str
    graph_runtime: str
    run_id: str | None = None
    persisted: bool = False


class AgentRunDetailResponse(BaseModel):
    """单次持久化 Agent 运行详情。"""

    run_id: str
    created_at: str
    message: str
    selected_product_ids: list[str] = Field(default_factory=list)
    route: str
    route_reasoning: str
    final_answer: str
    warnings: list[str] = Field(default_factory=list)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    parsed_intent: IntentParseResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)
    faq_result: FaqAskResponse | None = None
    compare_result: CompareResponse | None = None
    provider: str
    model: str
    graph_runtime: str
    persisted: bool = True


class AgentRunSummary(BaseModel):
    """持久化的 Agent 运行摘要。"""

    run_id: str
    created_at: str
    message: str
    route: str
    final_answer_preview: str
    warning_count: int
    tool_call_count: int
    selected_product_ids: list[str] = Field(default_factory=list)
    recommended_product_ids: list[str] = Field(default_factory=list)
    provider: str
    model: str


class AgentRunListResponse(BaseModel):
    """最近的 Agent 运行历史。"""

    backend: str
    items: list[AgentRunSummary] = Field(default_factory=list)
