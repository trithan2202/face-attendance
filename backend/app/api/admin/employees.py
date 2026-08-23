import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.repositories.department_repository import DepartmentRepository
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.repositories.shift_repository import ShiftRepository
from backend.app.schemas import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from backend.app.services.enrollment import TARGET_SAMPLES
from backend.app.core.logging import log_extra


router = APIRouter(
    prefix="/admin/employees",
    tags=["admin-employees"],
    dependencies=[Depends(get_current_admin)],
)
logger = logging.getLogger("face_attendance.employee")


def _not_found():
    return HTTPException(status_code=404, detail="Không tìm thấy nhân viên")


def _response(db, employee):
    sample_count, has_centroid = EmployeeRepository.enrollment_stats(db, employee.id)
    if sample_count >= TARGET_SAMPLES and has_centroid:
        enrollment_status = "COMPLETED"
    elif sample_count > 0 or has_centroid:
        enrollment_status = "INCOMPLETE"
    else:
        enrollment_status = "NOT_STARTED"
    return EmployeeResponse(
        **{
            column.name: getattr(employee, column.name)
            for column in employee.__table__.columns
            if column.name not in {"id"}
        },
        id=employee.id,
        department=employee.department.name if employee.department else None,
        enrollment_status=enrollment_status,
        sample_count=sample_count,
        has_centroid=has_centroid,
    )


@router.get("", response_model=list[EmployeeResponse])
def list_employees(
    search: str | None = Query(default=None, max_length=255),
    employee_status: str | None = Query(
        default=None, alias="status", pattern=r"^(ACTIVE|INACTIVE|PENDING_ENROLLMENT)$"
    ),
    db: Session = Depends(get_db),
):
    return [
        _response(db, employee)
        for employee in EmployeeRepository.list(db, search, employee_status)
    ]


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if employee is None:
        raise _not_found()
    return _response(db, employee)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    if EmployeeRepository.get_by_code(db, payload.employee_code):
        raise HTTPException(status_code=409, detail="Mã nhân viên đã tồn tại")
    if ShiftRepository.get_by_id(db, payload.shift_id) is None:
        raise HTTPException(status_code=422, detail="Ca làm không tồn tại")
    if (
        payload.department_id is not None
        and DepartmentRepository.get_by_id(db, payload.department_id) is None
    ):
        raise HTTPException(status_code=422, detail="Phòng ban không tồn tại")
    if EmployeeRepository.get_by_national_id(db, payload.national_id):
        raise HTTPException(status_code=409, detail="Số CCCD đã tồn tại")
    employee = EmployeeRepository.create(db, **payload.model_dump())
    db.commit()
    logger.info(
        "Employee created",
        extra=log_extra(
            "employee_created",
            employee_id=employee.id,
            employee_code=employee.employee_code,
            shift_id=employee.shift_id,
        ),
    )
    return _response(db, employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)
):
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if employee is None:
        raise _not_found()
    duplicate = EmployeeRepository.get_by_code(db, payload.employee_code)
    if duplicate is not None and duplicate.id != employee.id:
        raise HTTPException(status_code=409, detail="Mã nhân viên đã tồn tại")
    if ShiftRepository.get_by_id(db, payload.shift_id) is None:
        raise HTTPException(status_code=422, detail="Ca làm không tồn tại")
    if (
        payload.department_id is not None
        and DepartmentRepository.get_by_id(db, payload.department_id) is None
    ):
        raise HTTPException(status_code=422, detail="Phòng ban không tồn tại")
    duplicate_id = EmployeeRepository.get_by_national_id(db, payload.national_id)
    if duplicate_id is not None and duplicate_id.id != employee.id:
        raise HTTPException(status_code=409, detail="Số CCCD đã tồn tại")
    sample_count, has_centroid = EmployeeRepository.enrollment_stats(db, employee.id)
    if payload.status == "ACTIVE" and not (sample_count >= TARGET_SAMPLES and has_centroid):
        raise HTTPException(
            status_code=409,
            detail="Chỉ có thể kích hoạt sau khi đăng ký đủ khuôn mặt",
        )
    EmployeeRepository.update(db, employee, **payload.model_dump())
    db.commit()
    logger.info(
        "Employee updated",
        extra=log_extra(
            "employee_updated",
            employee_id=employee.id,
            employee_code=employee.employee_code,
            status=employee.status,
            shift_id=employee.shift_id,
        ),
    )
    return _response(db, employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if employee is None:
        raise _not_found()
    employee.status = "INACTIVE"
    db.commit()
    logger.info(
        "Employee deactivated",
        extra=log_extra(
            "employee_deactivated",
            employee_id=employee.id,
            employee_code=employee.employee_code,
        ),
    )
