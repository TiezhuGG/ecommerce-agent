from __future__ import annotations

import json
from typing import Any

from app.catalog.data import PRODUCT_CATALOG
from app.config import settings
from app.llm.service import (
    LLMRequestError,
    LLMServiceUnavailableError,
    request_json_object,
)
from app.schemas.intent import IntentParseResponse, IntentSearchFilters


class IntentServiceUnavailableError(RuntimeError):
    """意图解析服务当前不可用。"""


class IntentParseError(RuntimeError):
    """意图解析失败。"""


def _allowed_categories() -> list[str]:
    return sorted({product.category for product in PRODUCT_CATALOG})


def _allowed_brands() -> list[str]:
    return sorted({product.brand for product in PRODUCT_CATALOG})


def _intent_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "keyword": {"type": "string"},
            "category": {"type": "string", "enum": ["", *_allowed_categories()]},
            "brand": {"type": "string", "enum": ["", *_allowed_brands()]},
            "max_price": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "scenario": {"type": "string"},
            "priorities": {"type": "array", "items": {"type": "string"}},
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


def _infer_category_from_query(query: str) -> str:
    lowered = query.strip().lower()
    for alias in [
        "蓝牙耳机",
        "无线耳机",
        "耳机",
        "机械键盘",
        "键盘",
        "鼠标",
        "显示器",
        "屏幕",
        "移动固态硬盘",
        "移动硬盘",
        "固态硬盘",
        "ssd",
    ]:
        if alias in lowered:
            return _normalize_category(alias)
    return ""


def _infer_brand_from_query(query: str) -> str:
    lowered = query.strip().lower()
    for alias in [
        "苹果",
        "apple",
        "索尼",
        "sony",
        "三星",
        "samsung",
        "罗技g",
        "logitech g",
        "罗技",
        "logitech",
        "雷蛇",
        "razer",
        "华硕",
        "asus",
        "戴尔",
        "dell",
        "明基",
        "benq",
        "声阔",
        "soundcore",
        "闪迪",
        "sandisk",
        "西数",
        "wd_black",
        "西部数据",
        "金士顿",
        "kingston",
        "森海塞尔",
        "sennheiser",
    ]:
        if alias in lowered:
            return _normalize_brand(alias)
    return ""


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
    if not category:
        category = _infer_category_from_query(query)
    if not brand:
        brand = _infer_brand_from_query(query)

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
        applied_filters.append(f"预算上限：￥{max_price}")
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
        "keyword 要尽量保留对商品搜索有帮助的短语。"
        "reasoning_summary 只用一句中文解释你的理解，不要推荐具体商品。"
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


def parse_intent(query: str) -> IntentParseResponse:
    """调用 LLM 把自然语言需求转成结构化条件。"""

    try:
        result = request_json_object(
            system_prompt=_build_system_prompt(),
            user_prompt=_build_schema_instruction(query),
            schema_name="ecommerce_intent_parser",
            json_schema=_intent_schema(),
        )
    except LLMServiceUnavailableError as exc:
        raise IntentServiceUnavailableError(str(exc)) from exc
    except LLMRequestError as exc:
        raise IntentParseError(f"调用模型解析意图失败：{exc}") from exc

    provider = f"{result.provider} / {result.strategy}"
    return _normalize_result(query, result.data, provider)
