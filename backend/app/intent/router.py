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
    """把自然语言导购需求解析成结构化筛选条件。"""

    try:
        return parse_intent(payload.query)
    except IntentServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except IntentParseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
