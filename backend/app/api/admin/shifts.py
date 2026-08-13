from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.repositories.shift_repository import ShiftRepository
from backend.app.schemas import ShiftCreate, ShiftResponse, ShiftUpdate


router = APIRouter(
    prefix="/admin/shifts",
    tags=["admin-shifts"],
    dependencies=[Depends(get_current_admin)],
)


def _not_found():
    return HTTPException(status_code=404, detail="Không tìm thấy ca làm")


@router.get("", response_model=list[ShiftResponse])
def list_shifts(db: Session = Depends(get_db)):
    return ShiftRepository.list_all(db)


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: int, db: Session = Depends(get_db)):
    shift = ShiftRepository.get_by_id(db, shift_id)
    if shift is None:
        raise _not_found()
    return shift


@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(payload: ShiftCreate, db: Session = Depends(get_db)):
    if ShiftRepository.get_by_code(db, payload.code):
        raise HTTPException(status_code=409, detail="Mã ca làm đã tồn tại")
    shift = ShiftRepository.create(db, **payload.model_dump())
    db.commit()
    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
def update_shift(shift_id: int, payload: ShiftUpdate, db: Session = Depends(get_db)):
    shift = ShiftRepository.get_by_id(db, shift_id)
    if shift is None:
        raise _not_found()
    duplicate = ShiftRepository.get_by_code(db, payload.code)
    if duplicate is not None and duplicate.id != shift.id:
        raise HTTPException(status_code=409, detail="Mã ca làm đã tồn tại")
    ShiftRepository.update(db, shift, **payload.model_dump())
    db.commit()
    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(shift_id: int, db: Session = Depends(get_db)):
    shift = ShiftRepository.get_by_id(db, shift_id)
    if shift is None:
        raise _not_found()
    if ShiftRepository.employee_count(db, shift_id):
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa ca đang được gán cho nhân viên",
        )
    try:
        ShiftRepository.delete(db, shift)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ca làm đang được sử dụng")
