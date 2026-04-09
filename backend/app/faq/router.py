from fastapi import APIRouter

from app.faq.service import ask_faq
from app.schemas.faq import FaqAskRequest, FaqAskResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.post("/ask", response_model=FaqAskResponse)
async def ask_faq_endpoint(payload: FaqAskRequest) -> FaqAskResponse:
    """知识库查询接口。"""

    return ask_faq(payload.question)
