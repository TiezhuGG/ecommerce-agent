from fastapi import APIRouter, Depends, HTTPException, Query

from app.admin.security import is_admin_access_enabled, require_admin_access
from app.db.runtime_verifier import run_database_smoke_checks
from app.schemas.system import DatabaseSmokeResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/access/status")
async def get_admin_access_status() -> dict[str, bool]:
    return {
        "enabled": is_admin_access_enabled(),
    }


@router.post("/access/verify")
async def verify_admin_access(_: None = Depends(require_admin_access)) -> dict[str, bool]:
    return {
        "enabled": is_admin_access_enabled(),
        "verified": True,
    }


@router.post("/database/smoke-check", response_model=DatabaseSmokeResponse)
async def run_database_smoke_check(
    expect_backend: str | None = Query(default=None),
    _: None = Depends(require_admin_access),
) -> DatabaseSmokeResponse:
    normalized_expect_backend = (expect_backend or "").strip().lower() or None
    if normalized_expect_backend not in {None, "sqlite", "postgresql"}:
        raise HTTPException(status_code=400, detail="expect_backend 只支持 sqlite 或 postgresql。")

    try:
        report = run_database_smoke_checks(expect_backend=normalized_expect_backend)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DatabaseSmokeResponse(**report.to_dict())
