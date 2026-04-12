from fastapi import APIRouter, Depends, HTTPException

from app.admin.security import require_admin_access
from app.faq.service import (
    FaqAdminUnavailableError,
    FaqImportValidationError,
    FaqEntryNotFoundError,
    ask_faq,
    create_faq_entry,
    delete_faq_entry,
    export_faq_entries,
    import_faq_entries,
    list_faq_entries_admin,
    update_faq_entry,
)
from app.schemas.faq import (
    FaqAskRequest,
    FaqAskResponse,
    FaqDeleteResponse,
    FaqEntry,
    FaqEntryImportRequest,
    FaqEntryImportResponse,
    FaqEntryListResponse,
    FaqEntryUpsertRequest,
)

router = APIRouter(prefix="/faq", tags=["faq"])


@router.post("/ask", response_model=FaqAskResponse)
async def ask_faq_endpoint(payload: FaqAskRequest) -> FaqAskResponse:
    """知识库查询接口。"""

    return ask_faq(payload.question)


@router.get("/entries", response_model=FaqEntryListResponse)
async def list_faq_entries_endpoint(_: None = Depends(require_admin_access)) -> FaqEntryListResponse:
    """知识库条目列表。"""

    try:
        return list_faq_entries_admin()
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/entries/export", response_model=FaqEntryListResponse)
async def export_faq_entries_endpoint(_: None = Depends(require_admin_access)) -> FaqEntryListResponse:
    """导出知识库条目。"""

    try:
        return export_faq_entries()
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/entries/import", response_model=FaqEntryImportResponse)
async def import_faq_entries_endpoint(
    payload: FaqEntryImportRequest,
    _: None = Depends(require_admin_access),
) -> FaqEntryImportResponse:
    """导入知识库条目。"""

    try:
        return import_faq_entries(payload)
    except FaqImportValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/entries", response_model=FaqEntry)
async def create_faq_entry_endpoint(
    payload: FaqEntryUpsertRequest,
    _: None = Depends(require_admin_access),
) -> FaqEntry:
    """新增知识库条目。"""

    try:
        return create_faq_entry(payload)
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.put("/entries/{entry_id}", response_model=FaqEntry)
async def update_faq_entry_endpoint(
    entry_id: str,
    payload: FaqEntryUpsertRequest,
    _: None = Depends(require_admin_access),
) -> FaqEntry:
    """更新知识库条目。"""

    try:
        return update_faq_entry(entry_id, payload)
    except FaqEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.delete("/entries/{entry_id}", response_model=FaqDeleteResponse)
async def delete_faq_entry_endpoint(
    entry_id: str,
    _: None = Depends(require_admin_access),
) -> FaqDeleteResponse:
    """删除知识库条目。"""

    try:
        return delete_faq_entry(entry_id)
    except FaqEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FaqAdminUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
