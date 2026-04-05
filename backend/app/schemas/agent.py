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
    """Agent 启动前预检结果。"""

    status: str
    summary: str
    model: str
    base_url: str | None
    api_style: str
    openai_sdk_available: bool
    langgraph_available: bool
    catalog_total: int
    warnings: list[str]
    tools: list[AgentToolStatus]


class AgentToolCall(BaseModel):
    """Agent 在本轮对话中调用过的工具记录。"""

    tool_name: str
    status: str
    summary: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class AgentChatRequest(BaseModel):
    """Agent 对话请求。"""

    message: str = Field(..., min_length=1, description="用户输入的自然语言问题或导购需求。")
    selected_product_ids: list[str] = Field(
        default_factory=list,
        description="前端当前已选中的商品，用于帮助 Agent 进入商品对比场景。",
    )


class AgentChatResponse(BaseModel):
    """Agent 对话结果。"""

    message: str
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
