import json
from typing import Any

from app.catalog.data import PRODUCT_CATALOG
from app.config import settings
from app.schemas.intent import IntentParseResponse, IntentSearchFilters


class IntentServiceUnavailableError(RuntimeError):
    """意图解析服务当前不可用。"""


class IntentParseError(RuntimeError):
    """意图解析失败。"""


def _build_openai_client():
    """按配置创建客户端。

    这里故意只依赖“OpenAI 协议”而不依赖具体供应商。
    也就是说，后端并不关心你接的是 OpenAI、阿里、硅基流动还是其他兼容网关，
    只要它遵循 OpenAI 风格接口，我们就尽量用统一调用层去兼容。
    """

    if not settings.openai_api_key:
        raise IntentServiceUnavailableError(
            "未配置 OPENAI_API_KEY，当前无法使用 AI 意图解析。请先在 backend/.env 中补充配置。"
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise IntentServiceUnavailableError(
            "后端尚未安装 openai SDK。请先执行 `pip install -r backend/requirements.txt`。"
        ) from exc

    client_kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url

    return OpenAI(**client_kwargs)


def _allowed_categories() -> list[str]:
    return sorted({product.category for product in PRODUCT_CATALOG})


def _allowed_brands() -> list[str]:
    return sorted({product.brand for product in PRODUCT_CATALOG})


def _intent_schema() -> dict[str, Any]:
    """给结构化解析使用的 JSON Schema。"""

    return {
        "type": "object",
        "properties": {
            "keyword": {"type": "string"},
            "category": {"type": "string", "enum": ["", *_allowed_categories()]},
            "brand": {"type": "string", "enum": ["", *_allowed_brands()]},
            "max_price": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "scenario": {"type": "string"},
            "priorities": {
                "type": "array",
                "items": {"type": "string"},
            },
            "reasoning_summary": {"type": "string"},
        },
        "required": [
            "keyword",
            "category",
            "brand",
            "max_price",
            "scenario",
            "priorities",
            "reasoning_summary",
        ],
        "additionalProperties": False,
    }


def _normalize_category(value: str) -> str:
    normalized = value.strip()
    if normalized in _allowed_categories():
        return normalized

    alias_map = {
        "耳机": "蓝牙耳机",
        "蓝牙耳机": "蓝牙耳机",
        "无线耳机": "蓝牙耳机",
        "键盘": "机械键盘",
        "机械键盘": "机械键盘",
        "鼠标": "鼠标",
        "显示器": "显示器",
        "屏幕": "显示器",
        "固态硬盘": "移动固态硬盘",
        "ssd": "移动固态硬盘",
        "移动硬盘": "移动固态硬盘",
        "移动固态硬盘": "移动固态硬盘",
    }
    return alias_map.get(normalized.lower(), "")


def _normalize_brand(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""

    allowed_map = {brand.lower(): brand for brand in _allowed_brands()}
    if normalized.lower() in allowed_map:
        return allowed_map[normalized.lower()]

    alias_map = {
        "苹果": "Apple",
        "索尼": "Sony",
        "三星": "Samsung",
        "罗技": "Logitech",
        "罗技g": "Logitech G",
        "雷蛇": "Razer",
        "华硕": "ASUS",
        "戴尔": "Dell",
        "明基": "BenQ",
        "声阔": "soundcore",
        "闪迪": "SanDisk",
        "西数": "WD_BLACK",
        "西部数据": "WD_BLACK",
        "金士顿": "Kingston",
        "森海塞尔": "Sennheiser",
    }
    return alias_map.get(normalized.lower(), "")


def _normalize_result(query: str, raw_data: dict[str, Any], provider_name: str) -> IntentParseResponse:
    keyword = str(raw_data.get("keyword", "")).strip()
    category = _normalize_category(str(raw_data.get("category", "")))
    brand = _normalize_brand(str(raw_data.get("brand", "")))
    raw_max_price = raw_data.get("max_price")
    max_price = raw_max_price if isinstance(raw_max_price, int) and raw_max_price >= 0 else None
    scenario = str(raw_data.get("scenario", "")).strip()
    priorities = [str(item).strip() for item in raw_data.get("priorities", []) if str(item).strip()][:3]
    reasoning_summary = str(raw_data.get("reasoning_summary", "")).strip()

    if category and category not in _allowed_categories():
        category = ""
    if brand and brand not in _allowed_brands():
        brand = ""

    if not keyword:
        keyword = query.strip()

    applied_filters: list[str] = []
    if keyword:
        applied_filters.append(f"关键词：{keyword}")
    if category:
        applied_filters.append(f"分类：{category}")
    if brand:
        applied_filters.append(f"品牌：{brand}")
    if max_price is not None:
        applied_filters.append(f"预算上限：¥{max_price}")
    if scenario:
        applied_filters.append(f"场景：{scenario}")
    applied_filters.extend(f"优先级：{item}" for item in priorities)

    return IntentParseResponse(
        query=query,
        search_filters=IntentSearchFilters(
            keyword=keyword,
            category=category,
            brand=brand,
            max_price=max_price,
        ),
        scenario=scenario,
        priorities=priorities,
        applied_filters=applied_filters,
        reasoning_summary=reasoning_summary or "AI 已将自然语言需求整理为可执行的搜索条件。",
        provider=provider_name,
        model=settings.openai_model,
    )


def _build_system_prompt() -> str:
    return (
        "你是电商导购系统里的意图解析器。"
        "你的任务只有把用户的自然语言需求整理成结构化搜索条件。"
        "不要编造商品事实、库存、优惠、评分或评论。"
        "category 只能从给定分类里选择，brand 只能从给定品牌里选择；不确定时必须返回空字符串。"
        "keyword 要尽量保留对商品检索有帮助的短语。"
        "reasoning_summary 只用一句中文说明你的理解，不要推荐具体商品。"
    )


def _build_schema_instruction(query: str) -> str:
    categories = "、".join(_allowed_categories())
    brands = "、".join(_allowed_brands())
    schema = json.dumps(_intent_schema(), ensure_ascii=False)

    return (
        f"可选分类：{categories}\n"
        f"可选品牌：{brands}\n"
        f"用户需求：{query}\n"
        f"请严格按照下面的 JSON Schema 返回结果，不要输出额外解释：\n{schema}"
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    """尽量从模型输出里提取 JSON 对象。

    兼容模型返回格式不完全统一：
    1. 可能直接返回纯 JSON
    2. 可能包在 ```json 代码块里
    3. 可能前后夹带少量解释文字
    """

    content = text.strip()
    if not content:
        raise IntentParseError("模型没有返回可解析内容。")

    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise IntentParseError("模型返回的内容不是合法 JSON，无法继续解析。") from None
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise IntentParseError("模型返回的内容不是合法 JSON，无法继续解析。") from exc


def _request_with_responses_api(client, query: str) -> tuple[dict[str, Any], str]:
    """使用 Responses API 调用模型。

    适合支持 Responses API 的模型或网关。
    """

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_schema_instruction(query)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "ecommerce_intent_parser",
                "schema": _intent_schema(),
                "strict": True,
            }
        },
    )

    output_text = getattr(response, "output_text", "")
    if not output_text:
        raise IntentParseError("模型没有返回可解析的结构化内容。")

    return _extract_json_object(output_text), "OpenAI-Compatible Responses API"


def _request_with_chat_json_mode(client, query: str) -> tuple[dict[str, Any], str]:
    """使用 Chat Completions + json_object。

    这是最常见的 OpenAI 兼容实现方式，很多第三方网关都会优先支持这一种。
    """

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_schema_instruction(query)},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content if response.choices else ""
    return _extract_json_object(content or ""), "OpenAI-Compatible Chat JSON Mode"


def _request_with_chat_prompt_mode(client, query: str) -> tuple[dict[str, Any], str]:
    """使用最宽松的 Chat Completions + prompt 约束 JSON。

    有些兼容网关虽然支持 `/chat/completions`，但不支持 `response_format`。
    这时就退回到纯 prompt 约束，让它仍然返回 JSON。
    """

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {
                "role": "user",
                "content": (
                    f"{_build_schema_instruction(query)}\n"
                    "请只输出一个 JSON 对象，不要输出 Markdown、解释、标题或额外文本。"
                ),
            },
        ],
    )

    content = response.choices[0].message.content if response.choices else ""
    return _extract_json_object(content or ""), "OpenAI-Compatible Chat Prompt JSON Mode"


def _resolve_api_style() -> str:
    style = settings.openai_api_style.strip().lower()
    if style not in {"auto", "responses", "chat"}:
        raise IntentServiceUnavailableError(
            "OPENAI_API_STYLE 仅支持 auto、responses、chat 三种取值。"
        )
    return style


def _build_call_plan() -> list[tuple[str, Any]]:
    """根据配置决定调用顺序。

    `auto` 的设计目标不是偏向某一家供应商，而是尽量兼容更多 OpenAI 协议实现：
    1. 先尝试最常见的 Chat JSON 模式
    2. 再尝试更宽松的 Chat Prompt JSON 模式
    3. 最后尝试 Responses API

    如果用户明确指定 `responses` 或 `chat`，就按照指定风格优先执行。
    """

    style = _resolve_api_style()
    if style == "responses":
        return [
            ("responses", _request_with_responses_api),
            ("chat-json", _request_with_chat_json_mode),
            ("chat-prompt", _request_with_chat_prompt_mode),
        ]
    if style == "chat":
        return [
            ("chat-json", _request_with_chat_json_mode),
            ("chat-prompt", _request_with_chat_prompt_mode),
            ("responses", _request_with_responses_api),
        ]
    return [
        ("chat-json", _request_with_chat_json_mode),
        ("chat-prompt", _request_with_chat_prompt_mode),
        ("responses", _request_with_responses_api),
    ]


def parse_intent(query: str) -> IntentParseResponse:
    """调用兼容 OpenAI 协议的模型解析用户导购意图。

    这层的职责是把自然语言需求转成系统可执行的结构化条件，
    而不是直接返回商品事实。后续真正的商品结果仍然来自 `/products`。
    """

    client = _build_openai_client()
    failures: list[str] = []

    for strategy_name, request_fn in _build_call_plan():
        try:
            raw_data, provider_name = request_fn(client, query)
            return _normalize_result(query=query, raw_data=raw_data, provider_name=provider_name)
        except IntentParseError as exc:
            failures.append(f"{strategy_name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{strategy_name}: {type(exc).__name__}: {exc}")

    base_url = settings.openai_base_url or "https://api.openai.com/v1"
    detail = " | ".join(failures) if failures else "没有拿到任何可用返回。"
    raise IntentParseError(
        "调用模型解析意图失败。"
        f"当前配置 model={settings.openai_model}，base_url={base_url}，api_style={_resolve_api_style()}。"
        f"尝试记录：{detail}"
    )
