from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.schemas import SettingResponse, SettingUpdateRequest
from backend.app.services.settings_service import SettingsService


router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])


@router.get("", response_model=list[SettingResponse])
def list_settings(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return SettingsService.list_all(db)


@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    payload: SettingUpdateRequest,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        SettingsService.update(db, key, payload.value, admin.id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))

    for setting in SettingsService.list_all(db):
        if setting["key"] == key:
            return setting

    raise HTTPException(status_code=404, detail="Không tìm thấy tham số")
