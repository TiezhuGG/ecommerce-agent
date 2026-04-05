from fastapi import APIRouter

from app.faq.service import ask_faq
from app.schemas.faq import FaqAskRequest, FaqAskResponse

router = APIRouter(prefix="/faq", tags=["faq"])


@router.post("/ask", response_model=FaqAskResponse)
async def ask_faq_endpoint(payload: FaqAskRequest) -> FaqAskResponse:
    """售前 FAQ 工具接口。

    这个接口的角色和商品搜索接口类似：
    它先提供一个稳定的业务工具，后续 Agent 再来调用它，而不是直接让模型自由发挥。
    """

    return ask_faq(payload.question)
