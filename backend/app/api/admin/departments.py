import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.repositories.department_repository import DepartmentRepository
from backend.app.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from backend.app.core.logging import log_extra


router = APIRouter(
    prefix="/admin/departments",
    tags=["admin-departments"],
    dependencies=[Depends(get_current_admin)],
)
logger = logging.getLogger("face_attendance.department")


def _not_found():
    return HTTPException(status_code=404, detail="Không tìm thấy phòng ban")


def _response(db, department):
    return DepartmentResponse(
        id=department.id,
        code=department.code,
        name=department.name,
        manager_name=department.manager_name,
        employee_count=DepartmentRepository.employee_count(db, department.id),
        created_at=department.created_at,
        updated_at=department.updated_at,
    )


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return [
        _response(db, department)
        for department in DepartmentRepository.list_all(db)
    ]


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    department = DepartmentRepository.get_by_id(db, department_id)
    if department is None:
        raise _not_found()
    return _response(db, department)


@router.post(
    "", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED
)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    if DepartmentRepository.get_by_code(db, payload.code):
        raise HTTPException(status_code=409, detail="Mã phòng ban đã tồn tại")
    department = DepartmentRepository.create(db, **payload.model_dump())
    db.commit()
    logger.info(
        "Department created",
        extra=log_extra(
            "department_created",
            department_id=department.id,
            department_code=department.code,
        ),
    )
    return _response(db, department)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)
):
    department = DepartmentRepository.get_by_id(db, department_id)
    if department is None:
        raise _not_found()
    duplicate = DepartmentRepository.get_by_code(db, payload.code)
    if duplicate is not None and duplicate.id != department.id:
        raise HTTPException(status_code=409, detail="Mã phòng ban đã tồn tại")
    DepartmentRepository.update(db, department, **payload.model_dump())
    db.commit()
    logger.info(
        "Department updated",
        extra=log_extra(
            "department_updated",
            department_id=department.id,
            department_code=department.code,
        ),
    )
    return _response(db, department)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    department = DepartmentRepository.get_by_id(db, department_id)
    if department is None:
        raise _not_found()
    if DepartmentRepository.employee_count(db, department_id):
        raise HTTPException(
            status_code=409,
            detail="Không thể xóa phòng ban đang được gán cho nhân viên",
        )
    try:
        DepartmentRepository.delete(db, department)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Phòng ban đang được sử dụng")
    logger.info(
        "Department deleted",
        extra=log_extra("department_deleted", department_id=department_id),
    )
