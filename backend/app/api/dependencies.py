from fastapi import Cookie, Depends, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.repositories.admin_user_repository import AdminUserRepository


def get_current_admin(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
    )
    if not access_token:
        raise unauthorized
    try:
        payload = decode_access_token(access_token)
        admin_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized

    admin = AdminUserRepository.get_by_id(db, admin_id)
    if admin is None or not admin.is_active:
        raise unauthorized
    return admin
