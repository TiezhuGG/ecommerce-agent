from fastapi import APIRouter, Depends, HTTPException, Query

from app.admin.security import require_admin_access
from app.agent.service import (
    AgentExecutionError,
    AgentRunHistoryUnavailableError,
    AgentRunNotFoundError,
    AgentServiceUnavailableError,
    get_agent_run_detail,
    get_agent_thread_detail,
    get_agent_precheck,
    list_recent_agent_runs,
    list_recent_agent_threads,
    run_agent_chat,
)
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentPrecheckResponse,
    AgentRunDetailResponse,
    AgentRunListResponse,
    AgentThreadDetailResponse,
    AgentThreadListResponse,
)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/precheck", response_model=AgentPrecheckResponse)
async def get_agent_precheck_endpoint(_: None = Depends(require_admin_access)) -> AgentPrecheckResponse:
    """查看 Agent 当前是否具备运行条件。"""

    return get_agent_precheck()


@router.get("/runs", response_model=AgentRunListResponse)
async def list_agent_runs_endpoint(limit: int = Query(default=10, ge=1, le=20)) -> AgentRunListResponse:
    """查看最近已持久化的 Agent 运行记录。"""

    return list_recent_agent_runs(limit)


@router.get("/threads", response_model=AgentThreadListResponse)
async def list_agent_threads_endpoint(
    limit: int = Query(default=10, ge=1, le=20),
) -> AgentThreadListResponse:
    """查看最近活跃的 Agent 会话线程摘要。"""

    return list_recent_agent_threads(limit)


@router.get("/threads/{thread_id}", response_model=AgentThreadDetailResponse)
async def get_agent_thread_detail_endpoint(
    thread_id: str,
    limit: int = Query(default=20, ge=1, le=20),
) -> AgentThreadDetailResponse:
    """查看单条 Agent 会话线程详情。"""

    try:
        return get_agent_thread_detail(thread_id, limit)
    except AgentRunHistoryUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=AgentRunDetailResponse)
async def get_agent_run_detail_endpoint(run_id: str) -> AgentRunDetailResponse:
    """查看单次 Agent 运行详情。"""

    try:
        return get_agent_run_detail(run_id)
    except AgentRunHistoryUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat_endpoint(payload: AgentChatRequest) -> AgentChatResponse:
    """统一的 Agent 对话入口。"""

    try:
        return run_agent_chat(
            payload.message,
            payload.selected_product_ids,
            payload.conversation_context,
            payload.thread_id,
        )
    except AgentServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
