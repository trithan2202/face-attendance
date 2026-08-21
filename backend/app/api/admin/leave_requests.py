import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.database import get_db
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.repositories.leave_request_repository import (
    LeaveRequestRepository,
)
from backend.app.schemas import (
    LeaveDecisionRequest,
    LeaveDecisionResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
)
from backend.app.services.leave_service import LeaveService, leave_dates
from backend.app.core.logging import log_extra


router = APIRouter(prefix="/admin/leave-requests", tags=["admin-leave-requests"])
logger = logging.getLogger("face_attendance.leave")


def _not_found():
    return HTTPException(status_code=404, detail="Không tìm thấy đơn nghỉ phép")


def _response(leave, employee, created_by):
    return LeaveRequestResponse(
        id=leave.id,
        employee_id=employee.id,
        employee_code=employee.employee_code,
        full_name=employee.full_name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        total_days=len(list(leave_dates(leave))),
        reason=leave.reason,
        status=leave.status,
        created_by=created_by,
        decided_at=leave.decided_at,
        decision_note=leave.decision_note,
        created_at=leave.created_at,
    )


@router.get("", response_model=list[LeaveRequestResponse])
def list_leave_requests(
    employee_id: int | None = None,
    leave_status: str | None = Query(default=None, alias="status", max_length=20),
    date_from: date | None = None,
    date_to: date | None = None,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="Ngày bắt đầu phải trước ngày kết thúc"
        )
    rows = LeaveRequestRepository.list(
        db, employee_id, leave_status, date_from, date_to
    )
    return [_response(*row) for row in rows]


@router.post(
    "", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED
)
def create_leave_request(
    payload: LeaveRequestCreate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    employee = EmployeeRepository.get_by_id(db, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=422, detail="Nhân viên không tồn tại")
    if employee.status == "INACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo đơn nghỉ phép cho nhân viên đã ngưng hoạt động",
        )
    if LeaveRequestRepository.find_overlapping(
        db, payload.employee_id, payload.start_date, payload.end_date
    ):
        raise HTTPException(
            status_code=409,
            detail="Nhân viên đã có đơn nghỉ phép trùng khoảng thời gian này",
        )

    leave = LeaveRequestRepository.create(
        db,
        employee_id=payload.employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason.strip(),
        created_by_admin_id=admin.id,
    )
    db.commit()
    logger.info(
        "Leave request created",
        extra=log_extra(
            "leave_request_created",
            leave_id=leave.id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            leave_type=leave.leave_type,
        ),
    )
    return _response(leave, employee, admin.username)


@router.patch("/{leave_id}/decision", response_model=LeaveDecisionResponse)
def decide_leave_request(
    leave_id: int,
    payload: LeaveDecisionRequest,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        result = LeaveService.decide(db, leave_id, admin.id, payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise _not_found()
    leave, employee, applied, skipped = result
    return LeaveDecisionResponse(
        leave=_response(leave, employee, admin.username),
        applied_days=applied,
        skipped_days=skipped,
    )


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_request(
    leave_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    leave = LeaveRequestRepository.get_by_id(db, leave_id)
    if leave is None:
        raise _not_found()
    if leave.status != "PENDING":
        raise HTTPException(
            status_code=409, detail="Chỉ có thể xóa đơn đang chờ duyệt"
        )
    LeaveRequestRepository.delete(db, leave)
    db.commit()
    logger.info(
        "Leave request deleted",
        extra=log_extra("leave_request_deleted", leave_id=leave_id),
    )
