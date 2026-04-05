from fastapi import APIRouter, HTTPException

from app.intent.service import (
    IntentParseError,
    IntentServiceUnavailableError,
    parse_intent,
)
from app.schemas.intent import IntentParseRequest, IntentParseResponse

router = APIRouter(prefix="/intent", tags=["intent"])


@router.post("/parse", response_model=IntentParseResponse)
async def parse_intent_endpoint(payload: IntentParseRequest) -> IntentParseResponse:
    """自然语言导购意图解析接口。

    这是当前项目里第一次把 OpenAI SDK 正式接入业务链路。
    但它只负责把“用户想买什么”翻译成系统能执行的条件，
    真正的商品结果依旧来自稳定的业务工具接口。
    """

    try:
        return parse_intent(payload.query)
    except IntentServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except IntentParseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
