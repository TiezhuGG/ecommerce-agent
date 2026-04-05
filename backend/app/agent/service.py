from __future__ import annotations

import json
import sys
from typing import Any, Literal, TypedDict

from app.catalog.data import PRODUCT_CATALOG
from app.catalog.service import search_products
from app.compare.service import compare_products
from app.config import settings
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
    AgentPrecheckResponse,
    AgentToolCall,
    AgentToolStatus,
)
from app.schemas.compare import CompareResponse
from app.schemas.faq import FaqAskResponse
from app.schemas.intent import IntentParseResponse


AgentRoute = Literal["shopping", "faq", "compare"]


class AgentServiceUnavailableError(RuntimeError):
    """Agent 当前不可运行。"""


class AgentExecutionError(RuntimeError):
    """Agent 执行失败。"""


class AgentGraphState(TypedDict, total=False):
    message: str
    selected_product_ids: list[str]
    warnings: list[str]
    tool_calls: list[AgentToolCall]
    route: AgentRoute
    route_reasoning: str
    parsed_intent: IntentParseResponse | None
    recommended_product_ids: list[str]
    faq_result: FaqAskResponse | None
    compare_result: CompareResponse | None
    final_answer: str
    provider: str


def get_agent_precheck() -> AgentPrecheckResponse:
    """汇总 Agent 运行前的关键环境信息。"""

    warnings: list[str] = []
    openai_ready = is_openai_sdk_available() and bool(settings.openai_api_key)
    langgraph_ready = is_langgraph_available()

    if not is_openai_sdk_available():
        warnings.append("当前环境未安装 openai SDK，涉及模型推理的能力不可用。")
    if not settings.openai_api_key:
        warnings.append("未配置 OPENAI_API_KEY，意图解析和 LLM 文本生成不可用。")
    if not langgraph_ready:
        warnings.append("当前环境未安装 langgraph，/agent/chat 暂时无法运行图编排。")
    if not settings.openai_base_url:
        warnings.append("当前未设置 OPENAI_BASE_URL，将使用 SDK 默认地址。")
    if sys.version_info >= (3, 14):
        warnings.append("当前使用的是 Python 3.14；langchain-core 会输出兼容性警告，建议优先使用 Python 3.12 或 3.13。")

    status = "ready"
    summary = "Agent 运行条件完整，可执行 LangGraph 编排、意图解析和工具调用。"

    if not langgraph_ready:
        status = "blocked"
        summary = "LangGraph 依赖缺失，Agent 编排尚不可用。"
    elif not openai_ready:
        status = "degraded"
        summary = "基础业务工具可用，但 LLM 相关能力将退化或不可用。"

    tools = [
        AgentToolStatus(
            name="商品搜索",
            enabled=True,
            description="基于结构化条件过滤商品目录，是导购推荐的事实来源。",
        ),
        AgentToolStatus(
            name="FAQ 查询",
            enabled=True,
            description="回答售前政策、发票、保修、物流等规则问题。",
        ),
        AgentToolStatus(
            name="商品对比",
            enabled=True,
            description="对 2 到 3 个商品做规则化对比摘要。",
        ),
        AgentToolStatus(
            name="意图解析",
            enabled=openai_ready,
            description="把自然语言导购需求转成结构化筛选条件。",
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
        catalog_total=len(PRODUCT_CATALOG),
        warnings=warnings,
        tools=tools,
    )


def _append_tool_call(
    state: AgentGraphState,
    *,
    tool_name: str,
    status: str,
    summary: str,
    input_payload: dict[str, Any] | None = None,
    output_payload: dict[str, Any] | None = None,
) -> None:
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
    warnings = list(state.get("warnings", []))
    warnings.append(message)
    state["warnings"] = warnings


def _detect_route_by_rules(message: str, selected_product_ids: list[str]) -> tuple[AgentRoute | None, str]:
    normalized = message.strip().lower()

    if len(selected_product_ids) >= 2:
        return "compare", "前端已经选中了至少 2 个商品，优先进入商品对比流程。"

    faq_keywords = ["退货", "换货", "发票", "保修", "质保", "物流", "发货", "售后", "退款", "签收"]
    if any(keyword in message for keyword in faq_keywords):
        return "faq", "命中了售前政策与服务类关键词，适合走 FAQ 工具。"

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


def _classify_route_with_llm(message: str) -> tuple[AgentRoute, str, str]:
    result = request_json_object(
        system_prompt=(
            "你是电商导购 Agent 的路由分类器。"
            "shopping 用于导购、搜索、推荐、预算筛选；"
            "faq 用于发票、退换货、保修、物流等规则说明；"
            "compare 用于对比、比较、选哪个、差异分析。"
        ),
        user_prompt=(
            f"用户消息：{message}\n"
            "请输出 route 和 reasoning。"
        ),
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
    message = state["message"]
    selected_product_ids = state.get("selected_product_ids", [])

    route, reasoning = _detect_route_by_rules(message, selected_product_ids)
    if route:
        state["route"] = route
        state["route_reasoning"] = reasoning
        state["provider"] = "规则路由"
        _append_tool_call(
            state,
            tool_name="route_classifier",
            status="completed",
            summary=reasoning,
            input_payload={"message": message, "selected_product_ids": selected_product_ids},
            output_payload={"route": route, "provider": "规则路由"},
        )
        return state

    try:
        llm_route, llm_reasoning, provider = _classify_route_with_llm(message)
        state["route"] = llm_route
        state["route_reasoning"] = llm_reasoning
        state["provider"] = provider
        _append_tool_call(
            state,
            tool_name="route_classifier",
            status="completed",
            summary=llm_reasoning,
            input_payload={"message": message},
            output_payload={"route": llm_route, "provider": provider},
        )
        return state
    except (LLMServiceUnavailableError, LLMRequestError) as exc:
        state["route"] = "shopping"
        state["route_reasoning"] = "路由分类器不可用，默认进入导购搜索流程。"
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
    message = state["message"]
    parsed_intent: IntentParseResponse | None = None

    try:
        parsed_intent = parse_intent(message)
        state["parsed_intent"] = parsed_intent
        _append_tool_call(
            state,
            tool_name="intent_parse",
            status="completed",
            summary="已将自然语言导购需求解析为结构化筛选条件。",
            input_payload={"query": message},
            output_payload={"applied_filters": parsed_intent.applied_filters},
        )

        product_result = search_products(
            keyword=parsed_intent.search_filters.keyword,
            category=parsed_intent.search_filters.category,
            brand=parsed_intent.search_filters.brand,
            max_price=parsed_intent.search_filters.max_price,
        )
    except (IntentServiceUnavailableError, IntentParseError) as exc:
        _append_warning(state, f"意图解析失败，已退化为关键词搜索：{exc}")
        _append_tool_call(
            state,
            tool_name="intent_parse",
            status="failed",
            summary="意图解析失败，已退化为关键词搜索。",
            input_payload={"query": message},
            output_payload={},
        )
        product_result = search_products(keyword=message)

    # 当模型给出的 keyword 过窄时，第一次搜索可能会 0 结果。
    # 这里做一个最小放宽：保留分类、品牌、预算，只去掉关键词重新搜一次。
    # 这样既保留了结构化约束，也避免因为单个关键词过严导致前端看起来“完全搜不到”。
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
            _append_warning(state, "首次搜索结果过窄，已保留分类/品牌/预算并放宽关键词重新搜索。")
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
        state["final_answer"] = "当前没有找到符合条件的商品。你可以放宽预算、品牌或分类条件后再试一次。"
        return state

    try:
        answer = request_text(
            system_prompt=(
                "你是电商导购助手。"
                "请基于给定的结构化结果，输出简洁、可信的中文导购建议。"
                "不要编造库存、优惠、评分或不存在的参数。"
            ),
            user_prompt=(
                f"用户原始需求：{message}\n"
                f"解析结果：{state.get('parsed_intent').model_dump_json() if state.get('parsed_intent') else '无'}\n"
                f"候选商品：{json.dumps([product.model_dump() for product in top_products], ensure_ascii=False)}\n"
                "请输出 3 到 5 句中文说明，先总结需求，再说明推荐理由。"
            ),
        )
        state["final_answer"] = answer.text
        if state.get("provider") in {"规则路由", "规则降级"}:
            state["provider"] = answer.provider
    except (LLMServiceUnavailableError, LLMRequestError) as exc:
        _append_warning(state, f"导购总结生成失败，已使用模板回复：{exc}")
        names = "、".join(product.name for product in top_products)
        state["final_answer"] = (
            f"我先根据你的需求筛出了 {product_result.total} 个候选商品。"
            f"当前更值得优先查看的是：{names}。"
            "你可以继续结合价格、品牌和场景做下一轮筛选。"
        )

    return state


def _faq_node(state: AgentGraphState) -> AgentGraphState:
    result = ask_faq(state["message"])
    state["faq_result"] = result
    state["final_answer"] = result.answer
    _append_tool_call(
        state,
        tool_name="ask_faq",
        status="completed",
        summary=f"已返回 FAQ 结果，来源为 {result.source_label}。",
        input_payload={"question": state["message"]},
        output_payload={"source_label": result.source_label},
    )
    return state


def _infer_compare_ids_from_message(message: str) -> list[str]:
    lowered = message.lower()
    matched_ids: list[str] = []
    for product in PRODUCT_CATALOG:
        if product.name.lower() in lowered:
            matched_ids.append(product.id)
    return matched_ids


def _compare_node(state: AgentGraphState) -> AgentGraphState:
    selected_product_ids = state.get("selected_product_ids", [])
    candidate_ids = (
        selected_product_ids
        if len(selected_product_ids) >= 2
        else _infer_compare_ids_from_message(state["message"])
    )
    candidate_ids = list(dict.fromkeys(candidate_ids))[:3]

    if len(candidate_ids) < 2:
        _append_warning(state, "当前进入了商品对比流程，但还没有足够的商品可比。")
        _append_tool_call(
            state,
            tool_name="compare_products",
            status="skipped",
            summary="对比商品不足 2 个，已提示用户先选择商品。",
            input_payload={"candidate_ids": candidate_ids},
            output_payload={},
        )
        state["final_answer"] = "如果你想让我做商品对比，请先在列表里选中至少 2 个商品，或者在问题里明确写出两个商品型号。"
        return state

    result = compare_products(candidate_ids)
    state["compare_result"] = result
    state["recommended_product_ids"] = [product.id for product in result.compared_products]
    state["final_answer"] = result.summary
    _append_tool_call(
        state,
        tool_name="compare_products",
        status="completed",
        summary=f"已完成 {len(result.compared_products)} 个商品的对比分析。",
        input_payload={"product_ids": candidate_ids},
        output_payload={"price_gap": result.price_gap},
    )
    return state


def _decide_next_after_route(state: AgentGraphState) -> str:
    return state["route"]


def _synthesize_node(state: AgentGraphState) -> AgentGraphState:
    route = state.get("route", "shopping")

    if route == "faq" and state.get("faq_result"):
        faq_result = state["faq_result"]
        if faq_result.matched_entry:
            state["final_answer"] = (
                f"{faq_result.answer}\n\n"
                f"参考来源：{faq_result.source_label}\n"
                "如果你还想继续追问，我也可以基于同一主题继续帮你展开。"
            )
        return state

    if route == "compare" and state.get("compare_result"):
        compare_result = state["compare_result"]
        highlights = "\n".join(f"- {item}" for item in compare_result.highlights)
        state["final_answer"] = f"{compare_result.summary}\n\n关键结论：\n{highlights}"
        return state

    return state


def _build_graph():
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


def run_agent_chat(message: str, selected_product_ids: list[str]) -> AgentChatResponse:
    """执行一轮 LangGraph Agent 对话。"""

    precheck = get_agent_precheck()
    if precheck.status == "blocked":
        raise AgentServiceUnavailableError(precheck.summary)

    try:
        app = _build_graph()
        state = app.invoke(
            AgentGraphState(
                message=message.strip(),
                selected_product_ids=selected_product_ids,
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

    return AgentChatResponse(
        message=message.strip(),
        route=state.get("route", "shopping"),
        route_reasoning=state.get("route_reasoning", ""),
        final_answer=state.get("final_answer", "本轮未生成可展示结果。"),
        warnings=state.get("warnings", []),
        tool_calls=state.get("tool_calls", []),
        parsed_intent=state.get("parsed_intent"),
        recommended_product_ids=state.get("recommended_product_ids", []),
        faq_result=state.get("faq_result"),
        compare_result=state.get("compare_result"),
        provider=state.get("provider", "未知"),
        model=settings.openai_model,
        graph_runtime="langgraph",
    )
