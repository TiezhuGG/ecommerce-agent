from fastapi import APIRouter

from app.faq.service import ask_faq
from app.schemas.faq import FaqAskRequest, FaqAskResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.post("/ask", response_model=FaqAskResponse)
async def ask_faq_endpoint(payload: FaqAskRequest) -> FaqAskResponse:
    """售前 FAQ 工具接口。

    这类接口的价值在于先把稳定业务能力独立出来，
    后续 Agent 只负责判断什么时候调用它，而不是自己编规则。
    """

    return ask_faq(payload.question)
