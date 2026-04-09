from __future__ import annotations

import json
import sys
from typing import Any, Literal, TypedDict

from app.catalog.service import search_products
from app.compare.service import compare_products
from app.config import settings
from app.db.repositories import get_repositories
from app.db.service import (
    DatabaseUnavailableError,
    SQLAlchemyError,
    get_agent_run,
    list_agent_runs,
    persist_agent_run,
)
from app.faq.service import ask_faq
from app.intent.service import (
    IntentParseError,
    IntentServiceUnavailableError,
    parse_intent,
)
from app.llm.service import (
    LLMRequestError,
    LLMServiceUnavailableError,
    is_langgraph_available,
    is_openai_sdk_available,
    request_json_object,
    request_text,
)
from app.schemas.agent import (
    AgentChatResponse,
    AgentConversationTurn,
    AgentProviders,
    AgentRunDetailResponse,
    AgentRunListResponse,
    AgentRunSummary,
    AgentPrecheckResponse,
    AgentToolCall,
    AgentToolStatus,
)
from app.schemas.compare import CompareResponse
from app.schemas.faq import FaqAskResponse, FaqCitation
from app.schemas.intent import IntentParseResponse


AgentRoute = Literal["shopping", "faq", "compare"]


class AgentServiceUnavailableError(RuntimeError):
    """Agent 当前不可运行。"""


class AgentExecutionError(RuntimeError):
    """Agent 执行失败。"""


class AgentRunHistoryUnavailableError(RuntimeError):
    """Agent 运行历史当前不可用。"""


class AgentRunNotFoundError(RuntimeError):
    """指定的 Agent 运行记录不存在。"""


class AgentGraphState(TypedDict, total=False):
    """LangGraph 在节点之间传递的共享状态。"""

    message: str
    selected_product_ids: list[str]
    conversation_context: list[AgentConversationTurn]
    warnings: list[str]
    tool_calls: list[AgentToolCall]
    route: AgentRoute
    route_reasoning: str
    parsed_intent: IntentParseResponse | None
    recommended_product_ids: list[str]
    faq_result: FaqAskResponse | None
    compare_result: CompareResponse | None
    final_answer: str
    route_provider: str
    intent_provider: str
    answer_provider: str
    retrieval_provider: str
    provider: str


def get_agent_precheck() -> AgentPrecheckResponse:
    """汇总 Agent 运行前的关键环境信息。"""

    repositories = get_repositories()
    warnings: list[str] = []
    llm_ready = is_openai_sdk_available() and bool(settings.openai_api_key)
    langgraph_ready = is_langgraph_available()

    if not is_openai_sdk_available():
        warnings.append("当前环境未安装 openai SDK，模型分类与总结会退回本地规则或模板。")
    if not settings.openai_api_key:
        warnings.append("未配置 OPENAI_API_KEY，模型生成能力会退回本地规则或模板。")
    if not langgraph_ready:
        warnings.append("当前环境未安装 langgraph，/agent/chat 暂时无法执行图编排。")
    if not settings.openai_base_url:
        warnings.append("当前未配置 OPENAI_BASE_URL，将使用 SDK 默认地址。")
    if sys.version_info >= (3, 14):
        warnings.append(
            "当前使用的是 Python 3.14+，部分三方依赖可能输出兼容性警告，但基础链路仍可运行。"
        )
    if settings.database_url.strip() and not repositories.backend.startswith("sqlalchemy-"):
        warnings.append("已配置 DATABASE_URL，但当前数据库不可用，已回退到内存 seed 数据。")

    status = "ready"
    summary = "Agent 运行条件完整，可执行 LangGraph 编排、意图解析和业务工具调用。"

    if not langgraph_ready:
        status = "blocked"
        summary = "LangGraph 依赖缺失，Agent 编排暂不可用。"
    elif not llm_ready:
        status = "degraded"
        summary = "基础业务工具可用，模型相关节点会自动退回本地规则或模板。"

    tools = [
        AgentToolStatus(
            name="商品搜索",
            enabled=True,
            description="基于结构化条件过滤商品目录，是导购推荐的事实来源。",
        ),
        AgentToolStatus(
            name="知识库问答",
            enabled=True,
            description="回答发票、退换货、保修、物流等售前规则问题，内部已升级为 RAG 第一版。",
        ),
        AgentToolStatus(
            name="商品对比",
            enabled=True,
            description="对 2 到 3 个商品做规则化对比摘要。",
        ),
        AgentToolStatus(
            name="意图解析",
            enabled=True,
            description="优先使用模型解析自然语言导购需求，失败时自动退回本地规则。",
        ),
        AgentToolStatus(
            name="LangGraph 编排",
            enabled=langgraph_ready,
            description="按节点组织路由、工具调用与最终回复生成。",
        ),
    ]

    return AgentPrecheckResponse(
        status=status,
        summary=summary,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        api_style=settings.openai_api_style,
        openai_sdk_available=is_openai_sdk_available(),
        langgraph_available=langgraph_ready,
        data_backend=repositories.backend,
        agent_log_backend=repositories.backend if repositories.backend.startswith("sqlalchemy-") else "disabled",
        catalog_total=len(repositories.products.list_products()),
        warnings=warnings,
        tools=tools,
    )


def list_recent_agent_runs(limit: int = 10) -> AgentRunListResponse:
    """返回最近持久化的 Agent 运行记录。"""

    repositories = get_repositories()
    if not repositories.backend.startswith("sqlalchemy-"):
        return AgentRunListResponse(backend="disabled", items=[])

    try:
        rows = list_agent_runs(limit)
    except (DatabaseUnavailableError, SQLAlchemyError):
        return AgentRunListResponse(backend="disabled", items=[])

    items = [
        AgentRunSummary(
            run_id=str(row["run_id"]),
            created_at=str(row["created_at"]),
            message=str(row["message"]),
            route=str(row["route"]),
            final_answer_preview=str(row["final_answer"])[:140],
            warning_count=len(row["warnings"]) if isinstance(row["warnings"], list) else 0,
            tool_call_count=len(row["tool_calls"]) if isinstance(row["tool_calls"], list) else 0,
            selected_product_ids=list(row["selected_product_ids"])
            if isinstance(row["selected_product_ids"], list)
            else [],
            recommended_product_ids=list(row["recommended_product_ids"])
            if isinstance(row["recommended_product_ids"], list)
            else [],
            provider=str(row["provider"]),
            model=str(row["model"]),
        )
        for row in rows
    ]
    return AgentRunListResponse(backend=repositories.backend, items=items)


def get_agent_run_detail(run_id: str) -> AgentRunDetailResponse:
    """返回单次持久化 Agent 运行的完整详情。"""

    repositories = get_repositories()
    if not repositories.backend.startswith("sqlalchemy-"):
        raise AgentRunHistoryUnavailableError("当前未启用数据库日志存储，无法查看运行详情。")

    try:
        row = get_agent_run(run_id)
    except (DatabaseUnavailableError, SQLAlchemyError) as exc:
        raise AgentRunHistoryUnavailableError(f"当前无法读取 Agent 运行详情：{exc}") from exc

    if row is None:
        raise AgentRunNotFoundError(f"未找到 run_id={run_id} 对应的 Agent 运行记录。")

    return AgentRunDetailResponse(
        run_id=str(row["run_id"]),
        created_at=str(row["created_at"]),
        message=str(row["message"]),
        selected_product_ids=list(row["selected_product_ids"])
        if isinstance(row["selected_product_ids"], list)
        else [],
        conversation_context=[
            AgentConversationTurn(**item)
            for item in row.get("conversation_context", [])
            if isinstance(item, dict)
        ],
        route=str(row["route"]),
        route_reasoning=str(row.get("route_reasoning", "")),
        final_answer=str(row["final_answer"]),
        warnings=list(row["warnings"]) if isinstance(row["warnings"], list) else [],
        tool_calls=list(row["tool_calls"]) if isinstance(row["tool_calls"], list) else [],
        parsed_intent=row["parsed_intent"] if isinstance(row.get("parsed_intent"), dict) else None,
        recommended_product_ids=list(row["recommended_product_ids"])
        if isinstance(row["recommended_product_ids"], list)
        else [],
        faq_result=row["faq_result"] if isinstance(row.get("faq_result"), dict) else None,
        compare_result=row["compare_result"] if isinstance(row.get("compare_result"), dict) else None,
        providers=AgentProviders(**row["providers"]) if isinstance(row.get("providers"), dict) else AgentProviders(),
        provider=str(row["provider"]),
        model=str(row["model"]),
        graph_runtime=str(row.get("graph_runtime", "langgraph")),
        persisted=True,
    )


def _snapshot_providers(state: AgentGraphState) -> AgentProviders:
    return AgentProviders(
        route_provider=state.get("route_provider", ""),
        intent_provider=state.get("intent_provider", ""),
        answer_provider=state.get("answer_provider", ""),
        retrieval_provider=state.get("retrieval_provider", ""),
    )


def _summarize_provider(providers: AgentProviders) -> str:
    for value in (
        providers.answer_provider,
        providers.intent_provider,
        providers.route_provider,
        providers.retrieval_provider,
    ):
        if value:
            return value
    return "未知"


def _trim_conversation_context(
    conversation_context: list[AgentConversationTurn],
    limit: int = 4,
) -> list[AgentConversationTurn]:
    trimmed = [
        turn
        for turn in conversation_context
        if turn.user_message.strip() and turn.agent_answer.strip()
    ]
    return trimmed[-limit:]


def _format_conversation_context_text(conversation_context: list[AgentConversationTurn]) -> str:
    if not conversation_context:
        return "无历史上下文"

    lines: list[str] = []
    for index, turn in enumerate(conversation_context, start=1):
        route_label = f" / 路由：{turn.route}" if turn.route else ""
        lines.append(f"第 {index} 轮用户：{turn.user_message}")
        lines.append(f"第 {index} 轮Agent：{turn.agent_answer}{route_label}")
        if turn.selected_product_ids:
            lines.append(f"第 {index} 轮已选商品：{', '.join(turn.selected_product_ids)}")
        if turn.recommended_product_ids:
            lines.append(f"第 {index} 轮推荐商品：{', '.join(turn.recommended_product_ids)}")
    return "\n".join(lines)


def _build_contextual_query(message: str, conversation_context: list[AgentConversationTurn]) -> str:
    context_text = _format_conversation_context_text(conversation_context)
    if context_text == "无历史上下文":
        return message
    return (
        "以下是最近几轮对话上下文，请结合这些信息理解当前追问。\n"
        f"{context_text}\n"
        f"当前用户追问：{message}"
    )


def _collect_context_product_ids(conversation_context: list[AgentConversationTurn]) -> list[str]:
    collected: list[str] = []
    for turn in conversation_context:
        collected.extend(turn.selected_product_ids)
        collected.extend(turn.recommended_product_ids)
    return list(dict.fromkeys(collected))


def _append_tool_call(
    state: AgentGraphState,
    *,
    tool_name: str,
    status: str,
    summary: str,
    input_payload: dict[str, Any] | None = None,
    output_payload: dict[str, Any] | None = None,
) -> None:
    """向共享状态里追加一条工具调用轨迹。"""

    calls = list(state.get("tool_calls", []))
    calls.append(
        AgentToolCall(
            tool_name=tool_name,
            status=status,
            summary=summary,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
        )
    )
    state["tool_calls"] = calls


def _append_warning(state: AgentGraphState, message: str) -> None:
    """向共享状态里追加一条执行警告。"""

    warnings = list(state.get("warnings", []))
    warnings.append(message)
    state["warnings"] = warnings


def _detect_route_by_rules(
    message: str,
    selected_product_ids: list[str],
) -> tuple[AgentRoute | None, str]:
    """先用简单规则做第一层路由判断。"""

    normalized = message.strip().lower()

    if len(selected_product_ids) >= 2:
        return "compare", "前端已经选中了至少 2 个商品，优先进入商品对比流程。"

    faq_keywords = [
        "退货",
        "退款",
        "换货",
        "发票",
        "专票",
        "保修",
        "质保",
        "物流",
        "发货",
        "签收",
        "售后",
        "次日达",
    ]
    if any(keyword in message for keyword in faq_keywords):
        return "faq", "命中了售前政策与服务类关键词，更适合进入知识库问答流程。"

    compare_keywords = ["对比", "比较", "区别", "差别", "选哪个", "怎么选", "pk"]
    if any(keyword in normalized for keyword in compare_keywords):
        return "compare", "命中了商品比较类关键词，优先进入商品对比流程。"

    return None, ""


def _route_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": ["shopping", "faq", "compare"],
            },
            "reasoning": {"type": "string"},
        },
        "required": ["route", "reasoning"],
        "additionalProperties": False,
    }


def _classify_route_with_llm(
    message: str,
    conversation_context: list[AgentConversationTurn],
) -> tuple[AgentRoute, str, str]:
    """当规则不够确定时，再交给模型做路由分类。"""

    result = request_json_object(
        system_prompt=(
            "你是电商导购 Agent 的路由分类器。"
            "shopping 用于导购、搜索、推荐、预算筛选；"
            "faq 用于发票、退换货、保修、物流等规则说明；"
            "compare 用于对比、比较、选哪个、差异分析。"
        ),
        user_prompt=(f"用户消息：{message}\n请输出 route 和 reasoning。"),
        schema_name="agent_route_classifier",
        json_schema=_route_schema(),
    )

    route = str(result.data.get("route", "shopping")).strip()
    if route not in {"shopping", "faq", "compare"}:
        route = "shopping"

    reasoning = str(result.data.get("reasoning", "")).strip() or "模型判断当前消息更适合进入该流程。"
    provider = f"{result.provider} / {result.strategy}"
    return route, reasoning, provider


def _route_node(state: AgentGraphState) -> AgentGraphState:
    """决定当前问题应该走哪条业务链路。"""

    message = state["message"]
    selected_product_ids = state.get("selected_product_ids", [])
    conversation_context = state.get("conversation_context", [])

    route, reasoning = _detect_route_by_rules(message, selected_product_ids)
    if route:
        state["route"] = route
        state["route_reasoning"] = reasoning
        state["route_provider"] = "规则路由"
        state["provider"] = "规则路由"
        _append_tool_call(
            state,
            tool_name="route_classifier",
            status="completed",
            summary=reasoning,
            input_payload={
                "message": message,
                "selected_product_ids": selected_product_ids,
                "conversation_turns": len(conversation_context),
            },
            output_payload={"route": route, "provider": "规则路由"},
        )
        return state

    try:
        llm_route, llm_reasoning, provider = _classify_route_with_llm(
            _build_contextual_query(message, conversation_context),
            conversation_context,
        )
        state["route"] = llm_route
        state["route_reasoning"] = llm_reasoning
        state["route_provider"] = provider
        state["provider"] = provider
        _append_tool_call(
            state,
            tool_name="route_classifier",
            status="completed",
            summary=llm_reasoning,
            input_payload={"message": message, "conversation_turns": len(conversation_context)},
            output_payload={"route": llm_route, "provider": provider},
        )
        return state
    except (LLMServiceUnavailableError, LLMRequestError) as exc:
        state["route"] = "shopping"
        state["route_reasoning"] = "路由分类器不可用，默认进入导购搜索流程。"
        state["route_provider"] = "规则降级"
        state["provider"] = "规则降级"
        _append_warning(state, f"路由分类失败，已默认进入导购流程：{exc}")
        _append_tool_call(
            state,
            tool_name="route_classifier",
            status="failed",
            summary="路由分类失败，已降级为 shopping。",
            input_payload={"message": message},
            output_payload={"route": "shopping"},
        )
        return state


def _shopping_node(state: AgentGraphState) -> AgentGraphState:
    """导购节点：先做意图解析，再做商品搜索。"""

    message = state["message"]
    conversation_context = state.get("conversation_context", [])
    contextual_query = _build_contextual_query(message, conversation_context)
    parsed_intent: IntentParseResponse | None = None

    try:
        parsed_intent = parse_intent(contextual_query).model_copy(update={"query": message})
        state["parsed_intent"] = parsed_intent
        state["intent_provider"] = parsed_intent.provider
        intent_summary = "已将自然语言导购需求解析为结构化筛选条件。"
        if "fallback" in parsed_intent.provider.lower():
            intent_summary = "模型不可用，已退回本地规则提取结构化筛选条件。"
        _append_tool_call(
            state,
            tool_name="intent_parse",
            status="completed",
            summary=intent_summary,
            input_payload={"query": message, "conversation_turns": len(conversation_context)},
            output_payload={"applied_filters": parsed_intent.applied_filters},
        )

        product_result = search_products(
            keyword=parsed_intent.search_filters.keyword,
            category=parsed_intent.search_filters.category,
            brand=parsed_intent.search_filters.brand,
            max_price=parsed_intent.search_filters.max_price,
        )
    except (IntentServiceUnavailableError, IntentParseError) as exc:
        state["intent_provider"] = "intent-keyword-fallback"
        _append_warning(state, f"意图解析失败，已退化为关键词搜索：{exc}")
        _append_tool_call(
            state,
            tool_name="intent_parse",
            status="failed",
            summary="意图解析失败，已退化为关键词搜索。",
            input_payload={"query": message, "conversation_turns": len(conversation_context)},
            output_payload={},
        )
        product_result = search_products(keyword=message)

    # 模型给出的 keyword 偶尔会过窄，导致第一次搜索 0 结果。
    # 这里做一次最小放宽：保留分类、品牌和预算，只移除 keyword 重新搜索。
    if (
        product_result.total == 0
        and parsed_intent
        and parsed_intent.search_filters.keyword
        and (
            parsed_intent.search_filters.category
            or parsed_intent.search_filters.brand
            or parsed_intent.search_filters.max_price is not None
        )
    ):
        relaxed_result = search_products(
            category=parsed_intent.search_filters.category,
            brand=parsed_intent.search_filters.brand,
            max_price=parsed_intent.search_filters.max_price,
        )
        if relaxed_result.total > 0:
            product_result = relaxed_result
            _append_warning(state, "首次搜索结果过窄，已保留分类、品牌和预算并放宽关键词后重新搜索。")
            _append_tool_call(
                state,
                tool_name="search_products_relaxed",
                status="completed",
                summary=f"放宽关键词后重新搜索，得到 {relaxed_result.total} 个候选商品。",
                input_payload={
                    "keyword": "",
                    "category": parsed_intent.search_filters.category,
                    "brand": parsed_intent.search_filters.brand,
                    "max_price": parsed_intent.search_filters.max_price,
                },
                output_payload={"total": relaxed_result.total},
            )

    recommended_ids = [product.id for product in product_result.items[:3]]
    state["recommended_product_ids"] = recommended_ids

    search_input = {"keyword": message, "category": "", "brand": "", "max_price": None}
    if state.get("parsed_intent"):
        filters = state["parsed_intent"].search_filters
        search_input = {
            "keyword": filters.keyword,
            "category": filters.category,
            "brand": filters.brand,
            "max_price": filters.max_price,
        }

    _append_tool_call(
        state,
        tool_name="search_products",
        status="completed",
        summary=f"搜索到 {product_result.total} 个候选商品。",
        input_payload=search_input,
        output_payload={"total": product_result.total, "recommended_product_ids": recommended_ids},
    )

    top_products = product_result.items[:3]
    if not top_products:
        state["answer_provider"] = "shopping-no-results"
        state["final_answer"] = "当前没有找到符合条件的商品。你可以放宽预算、品牌或分类条件后再试一次。"
        return state

    try:
        parsed_intent_json = (
            state["parsed_intent"].model_dump_json()
            if state.get("parsed_intent")
            else "无"
        )
        answer = request_text(
            system_prompt=(
                "你是电商导购助手。"
                "请基于给定的结构化结果，输出简洁、可信的中文导购建议。"
                "不要编造库存、优惠、评分或不存在的参数。"
            ),
            user_prompt=(
                f"用户原始需求：{message}\n"
                f"解析结果：{parsed_intent_json}\n"
                f"候选商品：{json.dumps([product.model_dump() for product in top_products], ensure_ascii=False)}\n"
                "请输出 3 到 5 句中文说明，先总结需求，再说明推荐理由。"
            ),
        )
        state["final_answer"] = answer.text
        state["answer_provider"] = f"{answer.provider} / {answer.strategy}"
    except (LLMServiceUnavailableError, LLMRequestError) as exc:
        _append_warning(state, f"导购总结生成失败，已使用模板回复：{exc}")
        names = "、".join(product.name for product in top_products)
        state["answer_provider"] = "shopping-template-fallback"
        state["final_answer"] = (
            f"我先根据你的需求筛出了 {product_result.total} 个候选商品。"
            f"当前更值得优先查看的是：{names}。"
            "你可以继续结合价格、品牌和使用场景做下一轮筛选。"
        )

    return state


def _serialize_citations(citations: list[FaqCitation]) -> list[dict[str, Any]]:
    """把知识库引用整理成便于前端展示和调试的结构。"""

    return [
        {
            "entry_id": citation.entry_id,
            "title": citation.title,
            "snippet": citation.snippet,
            "source_label": citation.source_label,
            "score": citation.score,
        }
        for citation in citations
    ]


def _faq_node(state: AgentGraphState) -> AgentGraphState:
    """知识库节点：复用 FAQ / RAG 工具完成售前规则问答。"""

    conversation_context = state.get("conversation_context", [])
    result = ask_faq(_build_contextual_query(state["message"], conversation_context)).model_copy(
        update={"question": state["message"]}
    )
    state["faq_result"] = result
    state["retrieval_provider"] = result.retrieval_provider
    state["answer_provider"] = result.answer_provider
    state["final_answer"] = result.answer

    _append_tool_call(
        state,
        tool_name="ask_faq",
        status="completed",
        summary=f"已完成知识库检索，命中来源为 {result.source_label}。",
        input_payload={"question": state["message"], "conversation_turns": len(conversation_context)},
        output_payload={
            "source_label": result.source_label,
            "retrieval_mode": result.retrieval_mode,
            "retrieval_provider": result.retrieval_provider,
            "answer_provider": result.answer_provider,
            "citations": _serialize_citations(result.citations),
        },
    )
    return state


def _infer_compare_ids_from_message(message: str) -> list[str]:
    """当用户没有手动勾选商品时，尝试从问题里识别商品名称。"""

    lowered = message.lower()
    matched_ids: list[str] = []
    for product in get_repositories().products.list_products():
        if product.name.lower() in lowered:
            matched_ids.append(product.id)
    return matched_ids


def _compare_node(state: AgentGraphState) -> AgentGraphState:
    """对比节点：根据已选商品或问题文本生成对比结果。"""

    selected_product_ids = state.get("selected_product_ids", [])
    conversation_context = state.get("conversation_context", [])
    context_product_ids = _collect_context_product_ids(conversation_context)
    candidate_ids = (
        selected_product_ids
        if len(selected_product_ids) >= 2
        else _infer_compare_ids_from_message(state["message"])
    )
    if len(candidate_ids) < 2:
        candidate_ids = context_product_ids
    candidate_ids = list(dict.fromkeys(candidate_ids))[:3]

    if len(candidate_ids) < 2:
        state["answer_provider"] = "compare-needs-more-products"
        _append_warning(state, "当前进入了商品对比流程，但还没有足够的商品可比。")
        _append_tool_call(
            state,
            tool_name="compare_products",
            status="skipped",
            summary="对比商品不足 2 个，已提示用户先选择商品。",
            input_payload={
                "candidate_ids": candidate_ids,
                "conversation_turns": len(conversation_context),
                "context_product_ids": context_product_ids,
            },
            output_payload={},
        )
        state["final_answer"] = "如果你想让我做商品对比，请先在列表里选中至少 2 个商品，或者在问题里明确写出两个商品型号。"
        return state

    result = compare_products(candidate_ids)
    state["compare_result"] = result
    state["recommended_product_ids"] = [product.id for product in result.compared_products]
    state["answer_provider"] = "compare-rule-engine"
    state["final_answer"] = result.summary
    _append_tool_call(
        state,
        tool_name="compare_products",
        status="completed",
        summary=f"已完成 {len(result.compared_products)} 个商品的对比分析。",
        input_payload={
            "product_ids": candidate_ids,
            "conversation_turns": len(conversation_context),
            "context_product_ids": context_product_ids,
        },
        output_payload={"price_gap": result.price_gap},
    )
    return state


def _decide_next_after_route(state: AgentGraphState) -> str:
    """告诉 LangGraph 路由节点之后该走向哪个业务节点。"""

    return state["route"]


def _synthesize_node(state: AgentGraphState) -> AgentGraphState:
    """把工具结果整理成更适合前端直接展示的最终答复。"""

    route = state.get("route", "shopping")

    if route == "faq" and state.get("faq_result"):
        faq_result = state["faq_result"]
        citation_lines = "\n".join(
            f"- {citation.title}（{citation.source_label}）"
            for citation in faq_result.citations[:3]
        )

        final_answer = faq_result.answer
        if citation_lines:
            final_answer += f"\n\n检索模式：{faq_result.retrieval_mode}\n参考来源：\n{citation_lines}"
        if faq_result.suggestions:
            final_answer += f"\n\n可继续追问：{'；'.join(faq_result.suggestions)}"

        state["final_answer"] = final_answer
        return state

    if route == "compare" and state.get("compare_result"):
        compare_result = state["compare_result"]
        highlights = "\n".join(f"- {item}" for item in compare_result.highlights)
        state["final_answer"] = f"{compare_result.summary}\n\n关键结论：\n{highlights}"
        return state

    return state


def _build_graph():
    """构建 LangGraph 单 Agent 编排图。"""

    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise AgentServiceUnavailableError(
            "当前环境未安装 langgraph。请先执行 `pip install -r backend/requirements.txt`。"
        ) from exc

    graph = StateGraph(AgentGraphState)
    graph.add_node("route", _route_node)
    graph.add_node("shopping", _shopping_node)
    graph.add_node("faq", _faq_node)
    graph.add_node("compare", _compare_node)
    graph.add_node("synthesize", _synthesize_node)

    graph.set_entry_point("route")
    graph.add_conditional_edges(
        "route",
        _decide_next_after_route,
        {
            "shopping": "shopping",
            "faq": "faq",
            "compare": "compare",
        },
    )
    graph.add_edge("shopping", "synthesize")
    graph.add_edge("faq", "synthesize")
    graph.add_edge("compare", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def run_agent_chat(
    message: str,
    selected_product_ids: list[str],
    conversation_context: list[AgentConversationTurn] | None = None,
) -> AgentChatResponse:
    """执行一轮 LangGraph Agent 对话。"""

    precheck = get_agent_precheck()
    if precheck.status == "blocked":
        raise AgentServiceUnavailableError(precheck.summary)

    trimmed_conversation_context = _trim_conversation_context(conversation_context or [])

    try:
        app = _build_graph()
        state = app.invoke(
            AgentGraphState(
                message=message.strip(),
                selected_product_ids=selected_product_ids,
                conversation_context=trimmed_conversation_context,
                warnings=[],
                tool_calls=[],
                recommended_product_ids=[],
                provider="未执行",
            )
        )
    except AgentServiceUnavailableError:
        raise
    except Exception as exc:
        raise AgentExecutionError(f"运行 LangGraph Agent 失败：{exc}") from exc

    providers = _snapshot_providers(state)
    response = AgentChatResponse(
        message=message.strip(),
        selected_product_ids=list(selected_product_ids),
        conversation_context=trimmed_conversation_context,
        route=state.get("route", "shopping"),
        route_reasoning=state.get("route_reasoning", ""),
        final_answer=state.get("final_answer", "本轮未生成可展示结果。"),
        warnings=state.get("warnings", []),
        tool_calls=state.get("tool_calls", []),
        parsed_intent=state.get("parsed_intent"),
        recommended_product_ids=state.get("recommended_product_ids", []),
        faq_result=state.get("faq_result"),
        compare_result=state.get("compare_result"),
        providers=providers,
        provider=_summarize_provider(providers),
        model=settings.openai_model,
        graph_runtime="langgraph",
    )

    repositories = get_repositories()
    if repositories.backend.startswith("sqlalchemy-"):
        try:
            run_id = persist_agent_run(
                {
                    "message": response.message,
                    "route": response.route,
                    "route_reasoning": response.route_reasoning,
                    "final_answer": response.final_answer,
                    "warnings": response.warnings,
                    "tool_calls": [tool_call.model_dump() for tool_call in response.tool_calls],
                    "selected_product_ids": selected_product_ids,
                    "conversation_context": [turn.model_dump() for turn in response.conversation_context],
                    "recommended_product_ids": response.recommended_product_ids,
                    "parsed_intent": response.parsed_intent.model_dump() if response.parsed_intent else None,
                    "faq_result": response.faq_result.model_dump() if response.faq_result else None,
                    "compare_result": response.compare_result.model_dump() if response.compare_result else None,
                    "providers": response.providers.model_dump(),
                    "provider": response.provider,
                    "model": response.model,
                    "graph_runtime": response.graph_runtime,
                }
            )
            response.run_id = run_id
            response.persisted = True
        except (DatabaseUnavailableError, SQLAlchemyError) as exc:
            response.warnings.append(f"Agent 日志持久化失败，已跳过：{exc}")

    return response
