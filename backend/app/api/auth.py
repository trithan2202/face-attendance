from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, verify_password
from backend.app.core.logging import log_extra
from backend.app.repositories.admin_user_repository import AdminUserRepository
from backend.app.schemas import AdminResponse, LoginRequest


router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_NAME = "access_token"
logger = logging.getLogger("face_attendance.auth")


@router.post("/login", response_model=AdminResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    admin = AdminUserRepository.get_by_username(db, payload.username)
    if admin is None or not admin.is_active or not verify_password(
        payload.password, admin.password_hash
    ):
        logger.warning(
            "Admin login failed",
            extra=log_extra("admin_login_failed", username=payload.username),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )

    token = create_access_token(str(admin.id))
    admin.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=60 * settings.JWT_EXPIRE_MINUTES,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    logger.info(
        "Admin logged in",
        extra=log_extra(
            "admin_login_succeeded", admin_id=admin.id, username=admin.username
        ),
    )
    return admin


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax")
    logger.info("Admin logged out", extra=log_extra("admin_logout"))


@router.get("/me", response_model=AdminResponse)
def me(admin=Depends(get_current_admin)):
    return admin
