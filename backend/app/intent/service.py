from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings
from app.db.repositories import get_repositories
from app.llm.service import (
    LLMRequestError,
    LLMServiceUnavailableError,
    request_json_object,
)
from app.schemas.intent import IntentParseResponse, IntentSearchFilters


class IntentServiceUnavailableError(RuntimeError):
    """Raised when intent parsing is unavailable."""


class IntentParseError(RuntimeError):
    """Raised when intent parsing fails unexpectedly."""


def _allowed_categories() -> list[str]:
    return sorted({product.category for product in get_repositories().products.list_products()})


def _allowed_brands() -> list[str]:
    return sorted({product.brand for product in get_repositories().products.list_products()})


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
        "keyboard": "机械键盘",
        "键盘": "机械键盘",
        "机械键盘": "机械键盘",
        "mouse": "鼠标",
        "鼠标": "鼠标",
        "monitor": "显示器",
        "显示器": "显示器",
        "屏幕": "显示器",
        "portable ssd": "移动固态硬盘",
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
        "apple": "Apple",
        "苹果": "Apple",
        "sony": "Sony",
        "索尼": "Sony",
        "samsung": "Samsung",
        "三星": "Samsung",
        "logitech": "Logitech",
        "罗技": "Logitech",
        "logitech g": "Logitech G",
        "罗技g": "Logitech G",
        "razer": "Razer",
        "雷蛇": "Razer",
        "asus": "ASUS",
        "华硕": "ASUS",
        "dell": "Dell",
        "戴尔": "Dell",
        "benq": "BenQ",
        "明基": "BenQ",
        "soundcore": "soundcore",
        "声阔": "soundcore",
        "sandisk": "SanDisk",
        "闪迪": "SanDisk",
        "wd_black": "WD_BLACK",
        "wd black": "WD_BLACK",
        "西数": "WD_BLACK",
        "西部数据": "WD_BLACK",
        "kingston": "Kingston",
        "金士顿": "Kingston",
        "sennheiser": "Sennheiser",
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
        "ssd",
    ]:
        if alias in lowered:
            return _normalize_category(alias)
    return ""


def _infer_brand_from_query(query: str) -> str:
    lowered = query.strip().lower()
    for alias in [
        "apple",
        "苹果",
        "sony",
        "索尼",
        "samsung",
        "三星",
        "logitech g",
        "罗技g",
        "logitech",
        "罗技",
        "razer",
        "雷蛇",
        "asus",
        "华硕",
        "dell",
        "戴尔",
        "benq",
        "明基",
        "soundcore",
        "声阔",
        "sandisk",
        "闪迪",
        "wd_black",
        "wd black",
        "西数",
        "西部数据",
        "kingston",
        "金士顿",
        "sennheiser",
        "森海塞尔",
    ]:
        if alias in lowered:
            return _normalize_brand(alias)
    return ""


def _extract_max_price(query: str) -> int | None:
    patterns = [
        r"预算\s*(\d{2,5})",
        r"(\d{2,5})\s*(?:元|块)\s*(?:以内|以下|之内|内|左右)",
        r"(?:不超过|不要超过|低于|小于)\s*(\d{2,5})\s*(?:元|块)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, query)
        if not match:
            continue

        try:
            value = int(match.group(1))
        except ValueError:
            continue

        if value >= 0:
            return value

    return None


def _infer_scenario(query: str) -> str:
    scenario_map = {
        "通勤": ["通勤", "地铁", "公交"],
        "办公 / 会议": ["开会", "会议", "办公", "远程会议"],
        "游戏": ["游戏", "电竞", "fps", "lol", "瓦"],
        "设计 / 创作": ["设计", "修图", "剪辑", "创作"],
        "移动办公": ["便携", "出差", "移动办公", "随身"],
        "音乐": ["音乐", "听歌", "音质"],
    }

    matched: list[str] = []
    lowered = query.lower()
    for label, keywords in scenario_map.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            matched.append(label)

    return " / ".join(matched[:2])


def _infer_priorities(query: str) -> list[str]:
    priority_map = {
        "降噪": ["降噪", "安静"],
        "佩戴舒适": ["舒适", "久戴", "佩戴"],
        "高音质": ["音质", "高音质", "听歌"],
        "高性价比": ["性价比", "划算", "便宜"],
        "轻便": ["轻便", "便携", "轻巧"],
        "长续航": ["续航", "耐用", "电池"],
        "多设备切换": ["多设备", "切换", "双设备"],
        "静音": ["静音", "安静"],
        "低延迟": ["低延迟", "电竞", "游戏"],
    }

    matched: list[str] = []
    lowered = query.lower()
    for label, keywords in priority_map.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            matched.append(label)

    return matched[:3]


def _select_keyword(
    query: str,
    *,
    category: str,
    brand: str,
    priorities: list[str],
) -> str:
    if category:
        return category
    if brand:
        return brand

    keyword_candidates = [
        "4k",
        "降噪",
        "高音质",
        "轻便",
        "静音",
        "无线",
        "便携",
        "磁轴",
        "低延迟",
        "通勤",
        "办公",
        "游戏",
    ]
    lowered = query.lower()
    for candidate in keyword_candidates:
        if candidate in lowered:
            return candidate.upper() if candidate == "4k" else candidate

    if priorities:
        return priorities[0]

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
    if max_price is None:
        max_price = _extract_max_price(query)
    if not scenario:
        scenario = _infer_scenario(query)
    if not priorities:
        priorities = _infer_priorities(query)
    if not keyword:
        keyword = _select_keyword(query, category=category, brand=brand, priorities=priorities)

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
        reasoning_summary=reasoning_summary or "系统已将自然语言需求整理为可执行的搜索条件。",
        provider=provider_name,
        model=settings.openai_model,
    )


def _build_system_prompt() -> str:
    return (
        "你是电商导购系统里的意图解析器。"
        "你的任务只有把用户的自然语言需求整理成结构化搜索条件。"
        "不要编造商品事实、库存、优惠、评分或评论。"
        "category 只能从给定分类里选择，brand 只能从给定品牌里选择，不确定时必须返回空字符串。"
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


def _build_fallback_result(query: str, reason: str) -> IntentParseResponse:
    raw_data = {
        "keyword": "",
        "category": _infer_category_from_query(query),
        "brand": _infer_brand_from_query(query),
        "max_price": _extract_max_price(query),
        "scenario": _infer_scenario(query),
        "priorities": _infer_priorities(query),
        "reasoning_summary": (
            "模型解析不可用，已退回本地规则提取预算、品类、品牌和优先级。"
            if reason
            else "已使用本地规则提取结构化搜索条件。"
        ),
    }
    return _normalize_result(query, raw_data, "Local rules fallback")


def parse_intent(query: str) -> IntentParseResponse:
    """Parse natural language shopping intent into structured search filters."""

    try:
        result = request_json_object(
            system_prompt=_build_system_prompt(),
            user_prompt=_build_schema_instruction(query),
            schema_name="ecommerce_intent_parser",
            json_schema=_intent_schema(),
        )
    except (LLMServiceUnavailableError, LLMRequestError) as exc:
        return _build_fallback_result(query, str(exc))
    except Exception as exc:  # pragma: no cover - defensive guard
        raise IntentParseError(f"意图解析失败：{exc}") from exc

    provider = f"{result.provider} / {result.strategy}"
    return _normalize_result(query, result.data, provider)
