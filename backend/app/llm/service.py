from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any

from app.config import settings


class LLMServiceUnavailableError(RuntimeError):
    """当前环境无法建立可用的模型调用能力。"""


class LLMRequestError(RuntimeError):
    """模型调用已发起，但未得到可用结果。"""


@dataclass(slots=True)
class LLMJsonResult:
    data: dict[str, Any]
    provider: str
    strategy: str


@dataclass(slots=True)
class LLMTextResult:
    text: str
    provider: str
    strategy: str


def is_openai_sdk_available() -> bool:
    return find_spec("openai") is not None


def is_langgraph_available() -> bool:
    return find_spec("langgraph") is not None


def build_openai_client():
    """按配置创建兼容 OpenAI 协议的客户端。"""

    if not settings.openai_api_key:
        raise LLMServiceUnavailableError(
            "未配置 OPENAI_API_KEY，当前无法调用大模型。请先在 backend/.env 中补充配置。"
        )

    if not is_openai_sdk_available():
        raise LLMServiceUnavailableError(
            "后端尚未安装 openai SDK。请先执行 `pip install -r backend/requirements.txt`。"
        )

    from openai import OpenAI

    client_kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "timeout": 45.0,
    }
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url

    return OpenAI(**client_kwargs)


def resolve_api_style() -> str:
    style = settings.openai_api_style.strip().lower()
    if style not in {"auto", "responses", "chat"}:
        raise LLMServiceUnavailableError(
            "OPENAI_API_STYLE 仅支持 auto、responses、chat 三种取值。"
        )
    return style


def extract_json_object(text: str) -> dict[str, Any]:
    """尽量从模型输出中提取 JSON 对象。"""

    content = text.strip()
    if not content:
        raise LLMRequestError("模型没有返回可解析内容。")

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
            raise LLMRequestError("模型返回的内容不是合法 JSON，无法继续解析。") from None

        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMRequestError("模型返回的内容不是合法 JSON，无法继续解析。") from exc


def _provider_label() -> str:
    return "OpenAI-Compatible API"


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", "")
    if output_text:
        return output_text

    parts: list[str] = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            text = getattr(content_item, "text", None)
            if text:
                parts.append(text)
                continue

            if isinstance(content_item, dict):
                dict_text = content_item.get("text")
                if isinstance(dict_text, str) and dict_text.strip():
                    parts.append(dict_text)

    return "\n".join(parts).strip()


def _extract_chat_message_content(response: Any) -> str:
    if not getattr(response, "choices", None):
        return ""

    content = response.choices[0].message.content
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()

    return ""


def _request_json_with_chat_json_mode(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> LLMJsonResult:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = _extract_chat_message_content(response)
    return LLMJsonResult(
        data=extract_json_object(content),
        provider=_provider_label(),
        strategy="chat-json",
    )


def _request_json_with_chat_prompt_mode(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> LLMJsonResult:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"{user_prompt}\n"
                    "请只输出一个 JSON 对象，不要输出 Markdown、标题或额外解释。"
                ),
            },
        ],
    )
    content = _extract_chat_message_content(response)
    return LLMJsonResult(
        data=extract_json_object(content),
        provider=_provider_label(),
        strategy="chat-prompt",
    )


def _request_json_with_responses_api(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    json_schema: dict[str, Any],
) -> LLMJsonResult:
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": json_schema,
                "strict": True,
            }
        },
    )
    content = _extract_response_text(response)
    return LLMJsonResult(
        data=extract_json_object(content),
        provider=_provider_label(),
        strategy="responses",
    )


def _request_text_with_chat(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> LLMTextResult:
    response = client.chat.completions.create(
        model=model,
        temperature=0.4,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = _extract_chat_message_content(response).strip()
    if not content:
        raise LLMRequestError("模型没有返回文本结果。")
    return LLMTextResult(
        text=content,
        provider=_provider_label(),
        strategy="chat-text",
    )


def _request_text_with_responses(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> LLMTextResult:
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_prompt}],
            },
        ],
    )
    content = _extract_response_text(response).strip()
    if not content:
        raise LLMRequestError("模型没有返回文本结果。")
    return LLMTextResult(
        text=content,
        provider=_provider_label(),
        strategy="responses-text",
    )


def _format_attempt_error(attempts: list[str]) -> str:
    attempts_text = " | ".join(attempts) if attempts else "无"
    return (
        "调用模型失败。"
        f"当前配置 model={settings.openai_model}，"
        f"base_url={settings.openai_base_url or '默认'}，"
        f"api_style={resolve_api_style()}。"
        f"尝试记录：{attempts_text}"
    )


def request_json_object(
    *,
    system_prompt: str,
    user_prompt: str,
    schema_name: str,
    json_schema: dict[str, Any],
) -> LLMJsonResult:
    """请求模型返回一个 JSON 对象。"""

    client = build_openai_client()
    style = resolve_api_style()
    attempts: list[str] = []

    if style == "responses":
        strategies = ["responses"]
    elif style == "chat":
        strategies = ["chat-json", "chat-prompt"]
    else:
        strategies = ["chat-json", "chat-prompt", "responses"]

    for strategy in strategies:
        try:
            if strategy == "chat-json":
                return _request_json_with_chat_json_mode(
                    client=client,
                    model=settings.openai_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            if strategy == "chat-prompt":
                return _request_json_with_chat_prompt_mode(
                    client=client,
                    model=settings.openai_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            return _request_json_with_responses_api(
                client=client,
                model=settings.openai_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_name=schema_name,
                json_schema=json_schema,
            )
        except Exception as exc:
            attempts.append(f"{strategy}: {type(exc).__name__}: {exc}")

    raise LLMRequestError(_format_attempt_error(attempts))


def request_text(*, system_prompt: str, user_prompt: str) -> LLMTextResult:
    """请求模型返回自然语言文本。"""

    client = build_openai_client()
    style = resolve_api_style()
    attempts: list[str] = []

    strategies = ["chat-text", "responses-text"] if style != "responses" else ["responses-text"]

    for strategy in strategies:
        try:
            if strategy == "chat-text":
                return _request_text_with_chat(
                    client=client,
                    model=settings.openai_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            return _request_text_with_responses(
                client=client,
                model=settings.openai_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            attempts.append(f"{strategy}: {type(exc).__name__}: {exc}")

    raise LLMRequestError(_format_attempt_error(attempts))
