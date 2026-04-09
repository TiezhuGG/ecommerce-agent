from typing import Any

from pydantic import BaseModel, Field

from app.schemas.compare import CompareResponse
from app.schemas.faq import FaqAskResponse
from app.schemas.intent import IntentParseResponse


class AgentToolStatus(BaseModel):
    """Precheck-time tool status."""

    name: str
    enabled: bool
    description: str


class AgentPrecheckResponse(BaseModel):
    """Agent precheck result."""

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
    """Structured tool-call trace for one agent run."""

    tool_name: str
    status: str
    summary: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class AgentProviders(BaseModel):
    """Provider details used across agent stages."""

    route_provider: str = ""
    intent_provider: str = ""
    answer_provider: str = ""
    retrieval_provider: str = ""


class AgentConversationTurn(BaseModel):
    """One prior turn passed into the current agent run as conversation memory."""

    user_message: str = Field(..., min_length=1)
    agent_answer: str = Field(..., min_length=1)
    route: str = Field(default="")
    selected_product_ids: list[str] = Field(default_factory=list)
    recommended_product_ids: list[str] = Field(default_factory=list)


class AgentChatRequest(BaseModel):
    """Agent chat request."""

    message: str = Field(..., min_length=1, description="Current user message")
    selected_product_ids: list[str] = Field(
        default_factory=list,
        description="Currently selected products from the frontend workbench",
    )
    conversation_context: list[AgentConversationTurn] = Field(
        default_factory=list,
        description="Recent prior turns kept by the frontend session",
    )


class AgentChatResponse(BaseModel):
    """Agent chat result."""

    message: str
    selected_product_ids: list[str] = Field(default_factory=list)
    conversation_context: list[AgentConversationTurn] = Field(default_factory=list)
    route: str
    route_reasoning: str
    final_answer: str
    warnings: list[str]
    tool_calls: list[AgentToolCall]
    parsed_intent: IntentParseResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)
    faq_result: FaqAskResponse | None = None
    compare_result: CompareResponse | None = None
    providers: AgentProviders = Field(default_factory=AgentProviders)
    provider: str
    model: str
    graph_runtime: str
    run_id: str | None = None
    persisted: bool = False


class AgentRunDetailResponse(BaseModel):
    """Persisted agent run detail."""

    run_id: str
    created_at: str
    message: str
    selected_product_ids: list[str] = Field(default_factory=list)
    conversation_context: list[AgentConversationTurn] = Field(default_factory=list)
    route: str
    route_reasoning: str
    final_answer: str
    warnings: list[str] = Field(default_factory=list)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    parsed_intent: IntentParseResponse | None = None
    recommended_product_ids: list[str] = Field(default_factory=list)
    faq_result: FaqAskResponse | None = None
    compare_result: CompareResponse | None = None
    providers: AgentProviders = Field(default_factory=AgentProviders)
    provider: str
    model: str
    graph_runtime: str
    persisted: bool = True


class AgentRunSummary(BaseModel):
    """Persisted agent run summary."""

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
    """Recent persisted agent runs."""

    backend: str
    items: list[AgentRunSummary] = Field(default_factory=list)
