from fastapi import APIRouter, HTTPException

from app.agent.service import (
    AgentExecutionError,
    AgentServiceUnavailableError,
    get_agent_precheck,
    run_agent_chat,
)
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentPrecheckResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/precheck", response_model=AgentPrecheckResponse)
async def get_agent_precheck_endpoint() -> AgentPrecheckResponse:
    """查看 Agent 当前是否具备运行条件。"""

    return get_agent_precheck()


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat_endpoint(payload: AgentChatRequest) -> AgentChatResponse:
    """统一的 Agent 对话入口。"""

    try:
        return run_agent_chat(payload.message, payload.selected_product_ids)
    except AgentServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
