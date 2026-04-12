from fastapi import Header, HTTPException, status

from app.config import settings


ADMIN_ACCESS_HEADER = "X-Admin-Access-Code"


def is_admin_access_enabled() -> bool:
    return bool(settings.admin_access_code.strip())


def require_admin_access(
    x_admin_access_code: str | None = Header(default=None, alias=ADMIN_ACCESS_HEADER),
) -> None:
    configured_code = settings.admin_access_code.strip()
    if not configured_code:
        return

    if x_admin_access_code == configured_code:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="管理员访问码无效或缺失。",
    )
